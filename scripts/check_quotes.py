"""Check that the quotes are correctly formatted."""

import sys
import warnings
from pathlib import Path

from quotes import Folder

if __name__ == "__main__":
    with warnings.catch_warnings(record=True) as w:
        for path in Path(__file__).parent.parent.glob("**/0.json"):
            folder = Folder(path.parent)
            print(f"Checking {folder.path}...")
            folder.check()

        if w:
            sys.exit(1)
