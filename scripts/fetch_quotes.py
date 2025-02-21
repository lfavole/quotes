"""Fetch quotes from a Google Sheets document and add them in their corresponding folder."""

import csv
import os
import urllib.request
import warnings
from pathlib import Path

from quotes import Folder

BASE = Path(__file__).parent.parent.resolve()
URL = os.environ.get("GOOGLE_SHEETS_URL") or (BASE / ".google_sheets_url").read_text("utf-8").strip()


if __name__ == "__main__":
    print("Downloading file... ", end="")

    with urllib.request.urlopen(URL) as response:
        data = response.read()
    print("OK")

    reader = csv.DictReader(data.decode("utf-8").splitlines())

    print("Adding quotes... ", end="")
    quotes_count = 0
    for row in reader:
        folder_path = (BASE / row["Catégorie"]).resolve()
        if not folder_path.is_relative_to(BASE):
            warnings.warn(f"The path {row['Catégorie']} is suspicious, ignoring it", stacklevel=2)
            continue

        folder = Folder(folder_path)
        folder.add([
            row["Citation"],
            row["Auteur (la personne qui a dit la citation)"],
            row["Source (œuvre, chanson, ...)"],
        ])

        quotes_count += 1

    print(f"{quotes_count} quotes added")
    print("Now please delete all the records in the Google Sheets document.")
