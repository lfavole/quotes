# Static quotes API

This repository contains quotes available as JSON files.

## Folders structure

The quotes are in the `quotes` folder.

They are split in folders according to the language and the theme of the quotes.

For example, `fr/cats` contains French quotes about cats.

## Files structure

Each quotes folder contains a file named `0.json` with metadata about the quotes and files from `1.json` to `x.json` where x is a number.

The `0.json` file contains the following structure:
```json
{
    "total": 307,
    "chunk_size": 100,
}
```

- The `total` attribute contains the total number of quotes splitted across all the files.
- The `chunk_size` attribute contains the number of quotes in each file.

The other files have the following structure:
```json
[
    ["It always seems impossible until it's done.", "Nelson Mandela"],
    ["The key to a happy life is to accept you are never actually in control.", "Simon Masrani", "Jurassic World"],
    ["You can't change the world if you know what's hard and what's easy."]
    ...
]
```

They contain a list of quotes.

A quote is a list of three elements:
- The quote itself.
- The author.
- The reference (book, movie...).

The position of the elements matter and empty elements can be omitted.

NB: The author can be omitted but not the reference, e.g:
```json
["Rejection will never hurt for as long as regret.", "", "Some book"]
```
