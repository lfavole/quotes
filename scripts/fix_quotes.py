"""Fix the quotes in their folders."""

from pathlib import Path

from quotes import Folder

if __name__ == "__main__":
    for path in Path(__file__).parent.parent.glob("**/0.json"):
        folder = Folder(path.parent)
        print(f"Fixing {folder.path}...")
        folder.check()
        folder.fix()
        print()
