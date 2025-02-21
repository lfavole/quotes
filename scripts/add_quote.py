"""Prompt the user to add a quote."""

import sys
from pathlib import Path

from quotes import Folder

if __name__ == "__main__":
    path = Path(__file__).parent.parent / (sys.argv[1:] or [input("Folder: ")])[0]
    if not path.exists():
        print(f"The folder {path} doesn't exist, please create it beforehand")
        sys.exit(1)

    folder = Folder(path)

    quote = input("Quote: ").strip()
    author = input("Author: ").strip()
    book = input("Book: ").strip()

    item = [quote, author, book]
    while item and not item[-1]:
        item.pop()

    folder.add(item)
