# SQL eval questions

These draft questions use the checked-in museum sample. Review their wording and coverage before freezing a workshop run. Reference SQL and expected results are kept in the separate scorer image.

| ID | Difficulty | Question |
| --- | --- | --- |
| q01 | basic | How many artworks are in the museum sample? Return one count. |
| q02 | basic | How many artworks have a populated artist name? NULL, empty, and whitespace-only names are missing. Return one count. |
| q03 | basic | How many artworks have a missing artist name? Include NULL, empty, and whitespace-only names. Return one count. |
| q04 | basic | How many artworks are explicitly marked as public domain? Return one count. |
| q05 | basic | How many artworks have a populated primary image URL? NULL, empty, and whitespace-only URLs are missing. Return one count. |
| q06 | basic | How many artworks have no populated primary image URL? Include NULL, empty, and whitespace-only URLs. Return one count. |
| q07 | basic | How many artworks belong to the Asian Art department? Return one count. |
| q08 | basic | How many artworks have a populated classification? NULL, empty, and whitespace-only classifications are missing. Return one count. |
| q09 | basic | Return object ID and title for the five artworks with the smallest object IDs, in ascending ID order. |
| q10 | basic | How many artworks have a populated culture? NULL, empty, and whitespace-only culture values are missing. Return one count. |
| q11 | intermediate | Return every department and its artwork count, sorted by department name ascending. |
| q12 | intermediate | For each department with public-domain artworks, return department and public-domain artwork count, sorted by department ascending. |
| q13 | intermediate | For each department with missing artist names, return department and that count, sorted by department ascending. NULL, empty, and whitespace-only artist names are missing. |
| q14 | intermediate | For each department with populated primary image URLs, return department and that count, sorted by department ascending. NULL, empty, and whitespace-only URLs are missing. |
| q15 | intermediate | How many public-domain artworks are classified exactly as Paintings? Return one count. |
| q16 | intermediate | How many Asian Art artworks have a populated culture? NULL, empty, and whitespace-only cultures are missing. Return one count. |
| q17 | intermediate | How many artworks with a populated primary image URL are not explicitly marked public domain? NULL, empty, and whitespace-only URLs are missing. Return one count. |
| q18 | intermediate | Return the five departments with the most artworks as department and count, sorted by count descending, then department ascending for ties. |
| q19 | intermediate | Return object ID, title, and department for the five public-domain artworks with the smallest object IDs, sorted by ID ascending. |
| q20 | intermediate | For each department with populated classifications, return department and the number of distinct populated classifications, sorted by department ascending. NULL, empty, and whitespace-only classifications are missing. |
