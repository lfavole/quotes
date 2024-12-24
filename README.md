# Static quotes API

This repository contains quotes available as JSON files.

## Folders structure

The quotes are in the `quotes` folder.

They are split in folders according to the language and the theme of the quotes.

For example, `fr/cats` contains French quotes about cats.

## Files structure

Each quotes folder contains files from `0.json` to `x.json` where x is a number.

Each file has the following structure:
```json
{
    "total": 307,
    "end": false,
    "quotes": [
        ["It always seems impossible until it's done.", "Nelson Mandela"],
        ["The key to a happy life is to accept you are never actually in control.", "Simon Masrani", "Jurassic World"],
        ["You can't change the world if you know what's hard and what's easy."]
        ...
    ]
}
```

- The `total` attribute contains the total number of quotes splitted across all the files.
- The `end` attribute signals that the current file is the last file.
- The `quotes` attribute contains a list of all the quotes.

  A quote is a list of three elements:
  - The quote itself.
  - The author.
  - The reference (book, movie...).

  The position of the elements matter and empty elements can be omitted.

  NB: The author can be omitted but not the reference, e.g:
  ```json
  ["Rejection will never hurt for as long as regret.", "", "Some book"]
  ```
