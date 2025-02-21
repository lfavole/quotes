"""Check that the quotes are correctly formatted."""

from pathlib import Path

from quotes import Folder

if __name__ == "__main__":
    for path in Path(__file__).parent.parent.glob("**/0.json"):
        folder = Folder(path.parent)
        print(f"Checking {folder.path}...")
        folder.check()
