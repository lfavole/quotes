from contextlib import contextmanager
import json
from pathlib import Path
import warnings

MAX_QUOTES_PER_FILE = 100

class Folder:
    """A folder containing quotes."""
    def __init__(self, path: Path):
        self.path = path.resolve()

    @property
    def new_path(self):
        """The path to the temporary `new` folder when fixing quote files."""
        return (self.path / "new").resolve()

    def get_number(self, file: Path):
        """Returns the number included in the name of the given file. Will raise if there are any errors."""
        rel = file.relative_to(self.path)
        if len(rel.parts) != 1:
            raise ValueError(f"Too much path components in file {file}")

        if not rel.name.endswith(".json"):
            raise ValueError(f"File {file} doesn't end with .json")

        number = int(rel.name[:-5])
        if number < 0:
            raise ValueError(f"Number {number} in file {file} is negative")
        return number

    def get_number_safe(self, file: Path):
        """Returns the number included in the name of the given file or -1 if there were any errors."""
        try:
            return self.get_number(file)
        except ValueError:
            return -1

    def is_valid_file_name(self, file: Path):
        """Checks if the given file name is valid."""
        try:
            self.get_number(file)
            return True
        except ValueError:
            return False

    @contextmanager
    def open_file(self, file: Path, save=False):
        """Opens the given JSON file and optionally save it."""
        try:
            data = json.loads(file.read_text("utf-8"))
        except FileNotFoundError:
            data = {}
        yield data
        if save:
            with file.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    def get_files(self):
        """Returns the list of the files included in this folder."""
        files: list[Path] = []

        for item in sorted(self.path.iterdir(), key=self.get_number_safe):
            if item.is_file():
                item = item.resolve()

                if item.is_relative_to(self.new_path):
                    item.unlink()
                    continue

                if not self.is_valid_file_name(item):
                    warnings.warn(f"Invalid file name: {item}")
                files.append(item)

        return files

    def get_items(self, data):
        """Returns the quotes list in a JSON file."""
        return data.get("items", data) if isinstance(data, dict) else data

    def get_total(self, files: list[Path] | None = None):
        """Returns the total number of quotes in the given files."""
        files = files or self.get_files()
        total = 0

        for file in files:
            with self.open_file(file) as data:
                total += len(self.get_items(data))

        return total

    def fix_item(self, item: str):
        """Fix a quote item (quote, author, ...) by removing non-ASCII characters."""
        return item.replace("\xa0", " ").replace("\u2019", "'").replace("\xab ", '"').replace(" \xbb", '"')

    def fix_quotes(self, quotes: list):
        """Fix the quotes by removing non-ASCII characters."""
        ret = []
        for quote in quotes:
            ret.append([self.fix_item(item) for item in quote])
        return ret

    def check(self):
        """Checks if the current quotes folder is valid and coherent."""

        # If there is no folder, stop here
        if not self.path.exists():
            return

        files = self.get_files()
        total = self.get_total(files)

        # Check the structure and the total and end attributes
        for i, file in enumerate(files, start=-len(files)):
            with self.open_file(file) as data:
                if not isinstance(data, dict):
                    warnings.warn(f"No dict structure in file {file}")
                    data = {"items": data}

                if "items" not in data:
                    warnings.warn(f"No items section in file {file}")

                if data.get("total", 0) != total:
                    warnings.warn(f"Total of {data.get('total', 0)} doesn't match the length of {total}")

                number_of_items = len(self.get_items(data))
                if number_of_items > MAX_QUOTES_PER_FILE or i != -1 and number_of_items < MAX_QUOTES_PER_FILE:
                    warnings.warn(f"Total of {number_of_items} doesn't match the maximum quotes number of {MAX_QUOTES_PER_FILE}")

                if i != -1 and data.get("end") is not False:
                    warnings.warn(f"No end: false attribute in file {file}")
                if i == -1 and data.get("end") is not True:
                    warnings.warn(f"No end: true attribute in file {file}")

                for quote in self.get_items(data):
                    for item in quote:
                        if self.fix_item(item) != item:
                            warnings.warn(f"Item '{item}' contains non-ASCII characters")

    def fix(self):
        """Fixes the current quotes folder."""
        self.new_path.mkdir(parents=True, exist_ok=True)

        files = self.get_files()
        total = self.get_total(files)

        # Check the quotes number, split between files
        filename_index = 0
        stack = []

        def fill_file(end=False):
            """
            Add `MAX_QUOTES_NUMBER` quotes in `new/x.json` where `x` is a counter.

            If `end` is `True`, add all the remaining quotes.
            """
            nonlocal filename_index, stack
            if stack and (end or len(stack) > MAX_QUOTES_PER_FILE):
                with self.open_file(self.new_path / f"{filename_index}.json", save=True) as data:
                    data["total"] = total
                    data["end"] = end
                    data["items"], stack = stack[:MAX_QUOTES_PER_FILE], stack[MAX_QUOTES_PER_FILE:]
                    data["items"] = self.fix_quotes(data["items"])
                    filename_index += 1
                return True
            return False

        for file in files:
            with self.open_file(file) as data:
                stack.extend(self.get_items(data))
                fill_file()
                # Remove the old file
                file.unlink()

        # Add the quotes into the corresponding files
        while fill_file():
            pass
        fill_file(end=True)

        # Add the new files instead of the old ones
        for file in self.new_path.iterdir():
            file.rename(file.parent.parent / file.name)
        self.new_path.rmdir()

    def add(self, quote: list[str]):
        file = self.get_files()[-1]

        with self.open_file(file, True) as data:
            if len(data["items"]) >= MAX_QUOTES_PER_FILE:
                file = self.path / f"{self.get_number(file) + 1}.json"

        with self.open_file(file, save=True) as data:
            if "items" not in data:
                data["items"] = []
            data["items"].append(quote)

        with warnings.catch_warnings(action="ignore"):
            self.check()
            self.fix()
