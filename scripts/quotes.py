"""A module to manage quotes."""

import json
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeVar, cast, overload

MAX_QUOTES_PER_FILE = 100

T = TypeVar("T")


class Folder:
    """A folder containing quotes."""

    def __init__(self, path: Path) -> None:
        """Create a new `Folder`."""
        self.path = path.resolve()

    @property
    def new_path(self) -> Path:
        """The path to the temporary `new` folder when fixing quote files."""
        return (self.path / "new").resolve()

    def get_number(self, file: Path, zero_ok: bool = False) -> int:
        """
        Return the number included in the name of the given file.

        Raises:
            ValueError: if the file is in the wrong place, has the wrong extension or has a wrong number.

        """
        rel = file.relative_to(self.path)
        if len(rel.parts) != 1:
            msg = f"Too much path components in file {file}"
            raise ValueError(msg)

        if not rel.name.endswith(".json"):
            msg = f"File {file} doesn't end with .json"
            raise ValueError(msg)

        number = int(rel.name[:-5])
        if zero_ok and number == 0:
            return number
        if number <= 0:
            msg = f"Number {number} in file {file} is negative or null"
            raise ValueError(msg)
        return number

    def get_number_safe(self, file: Path) -> int:
        """Return the number included in the name of the given file or -1 if there were any errors."""
        try:
            return self.get_number(file)
        except ValueError:
            return -1

    def is_valid_file_name(self, file: Path) -> bool:
        """Check if the given file name is valid."""
        try:
            self.get_number(file)
        except ValueError:
            return False
        else:
            return True

    @overload
    @staticmethod
    @contextmanager
    def open_file(
        file: Path,
        datatype: type[T],
        save: bool = False,
    ) -> Generator[T, None, None]: ...

    @overload
    @staticmethod
    @contextmanager
    def open_file(
        file: Path,
        datatype: None = None,
        save: bool = False,
    ) -> Generator[dict[str, Any] | list[list[str]], None, None]: ...

    @staticmethod
    @contextmanager
    def open_file(
        file: Path,
        datatype: type[T] | None = None,
        save: bool = False,
    ) -> Generator[T, None, None]:
        """
        Open the given JSON file and optionally `save` it.

        Raises:
            TypeError: if the data has a wrong type (not dict/list).

        """
        try:
            data = json.loads(file.read_text("utf-8"))
        except FileNotFoundError:
            data = {}
        if not isinstance(data, dict | list):
            msg = f"Wrong type for data in {file}"
            raise TypeError(msg)
        data = cast("dict[str, Any] | list[list[str]]", data)
        if datatype is dict and isinstance(data, list):
            data = {"items": data}
        if datatype is list and isinstance(data, dict):
            data = data.get("items", [])
        yield data  # type: ignore[reportReturnType]
        if save:
            with file.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    def get_files(self) -> list[Path]:
        """Return the list of the files included in this folder."""
        files: list[Path] = []

        for item in sorted(self.path.iterdir(), key=self.get_number_safe):
            if item.is_file():
                item = item.resolve()  # noqa: PLW2901

                if item.is_relative_to(self.new_path):
                    item.unlink()
                    continue

                if not self.is_valid_file_name(item):
                    if self.get_number(item, zero_ok=True) == 0:
                        continue
                    warnings.warn(f"Invalid file name: {item}", stacklevel=2)
                files.append(item)

        return files

    @staticmethod
    def get_items(data: dict[str, Any] | list[list[str]]) -> list[list[str]]:
        """Return the quotes list in a JSON file."""
        return data.get("items", data) if isinstance(data, dict) else data

    def get_total(self, files: list[Path] | None = None) -> int:
        """Return the total number of quotes in the given files."""
        files = files or self.get_files()
        total = 0

        index_file = self.path / "0.json"

        with self.open_file(index_file, datatype=dict[str, Any]) as data:
            if data.get("items") is not None:
                files = [index_file, *files]

        for file in files:
            with self.open_file(file, datatype=list[list[str]]) as data:
                total += len(self.get_items(data))

        return total

    @staticmethod
    def fix_item(item: str) -> str:
        """Fix a quote item (quote, author, ...) by removing non-ASCII characters."""
        return item.replace("\xa0", " ").replace("\u2019", "'").replace("\xab ", '"').replace(" \xbb", '"')

    def fix_quotes(self, quotes: list[list[str]]) -> list[list[str]]:
        """Fix the quotes by removing non-ASCII characters."""
        return [[self.fix_item(item) for item in quote] for quote in quotes]

    def check(self) -> None:
        """Check if the current quotes folder is valid and coherent."""
        # If there is no folder, stop here
        if not self.path.exists():
            return

        files = self.get_files()
        total = self.get_total(files)

        index_file = self.path / "0.json"
        with self.open_file(index_file) as old_data:
            if not isinstance(old_data, dict):
                warnings.warn(f"No dict structure in file {index_file}", stacklevel=2)
                data: dict[str, Any] = {"items": old_data}
            else:
                data = old_data

            if data.get("total", 0) != total:
                warnings.warn(f"Total of {data['total']} doesn't match the length of {total}", stacklevel=2)

            if data.get("items") is not None:
                warnings.warn(f"Items section in file {index_file}", stacklevel=2)

        for i, file in enumerate(files, start=-len(files)):
            self.check_file(file, last=i == -1)

    def check_file(self, file: Path, last: bool = False) -> None:
        """Check the structure and the total and end attributes in a quotes file."""
        with self.open_file(file) as old_data:
            if isinstance(old_data, dict):
                warnings.warn(f"Dict structure in file {file}", stacklevel=2)
                if "items" not in old_data:
                    warnings.warn(f"No items section in file {file}", stacklevel=2)
                data: list[list[str]] = old_data.get("items", [])
            else:
                data = old_data

            number_of_items = len(self.get_items(data))
            if number_of_items > MAX_QUOTES_PER_FILE or (not last and number_of_items < MAX_QUOTES_PER_FILE):
                warnings.warn(
                    f"Total of {number_of_items} doesn't match the maximum quotes number of {MAX_QUOTES_PER_FILE}",
                    stacklevel=2,
                )

            for quote in self.get_items(data):
                for item in quote:
                    if self.fix_item(item) != item:
                        warnings.warn(f"Item '{item}' contains non-ASCII characters", stacklevel=2)

    def fix(self) -> None:
        """Fix the current quotes folder."""
        self.new_path.mkdir(parents=True, exist_ok=True)

        files = self.get_files()
        total = self.get_total(files)

        index_file = self.path / "0.json"
        with self.open_file(index_file, datatype=dict[str, Any], save=True) as data:
            if data.get("items") is not None:
                files.insert(0, index_file)

        # Check the quotes number, split between files
        filename_index = 1
        stack: list[list[str]] = []

        def fill_file(end: bool = False) -> bool:
            """
            Add `MAX_QUOTES_NUMBER` quotes in `new/x.json` where `x` is a counter.

            If `end` is `True`, add all the remaining quotes.
            """
            nonlocal filename_index, stack
            if stack and (end or len(stack) > MAX_QUOTES_PER_FILE):
                with self.open_file(
                    self.new_path / f"{filename_index}.json",
                    datatype=list[list[str]],
                    save=True,
                ) as data:
                    data[:], stack = stack[:MAX_QUOTES_PER_FILE], stack[MAX_QUOTES_PER_FILE:]
                    filename_index += 1
                return True
            return False

        for file in files:
            with self.open_file(file, datatype=list[list[str]]) as data:
                stack.extend(self.get_items(data))
                fill_file()
                # Remove the old file
                file.unlink()

        # Create the 0.json file with the total attribute
        with self.open_file(self.new_path / "0.json", datatype=dict[str, Any], save=True) as data:
            data["total"] = total
            data["chunk_size"] = MAX_QUOTES_PER_FILE

        # Add the quotes into the corresponding files
        while fill_file():
            pass
        fill_file(end=True)

        # Add the new files instead of the old ones
        for file in self.new_path.iterdir():
            file.rename(file.parent.parent / file.name)
        self.new_path.rmdir()

    def add(self, quote: list[str]) -> None:
        """Add a quote to the folder."""
        file = self.get_files()[-1]

        with self.open_file(file, datatype=list[list[str]], save=True) as data:
            if len(data) >= MAX_QUOTES_PER_FILE:
                file = self.path / f"{self.get_number(file) + 1}.json"

        with self.open_file(file, datatype=list[list[str]], save=True) as data:
            data.append(quote)

        with warnings.catch_warnings(action="ignore"):
            self.check()
            self.fix()
