---
type: reference
tags: [databases]
---
# SQL Joins Reference

## Join types

- INNER JOIN returns rows with a match in both tables.
- LEFT JOIN returns every row from the left table, with NULLs where the right has no match.
- FULL OUTER JOIN returns every row from both tables.
- CROSS JOIN returns every combination of rows.

## Common mistakes

- Forgetting a join condition multiplies rows and produces duplicates.
- Filtering the right table in WHERE turns a LEFT JOIN into an INNER JOIN. Put the filter in the ON clause.

## Window functions

ROW_NUMBER, RANK and LAG compute values across related rows without collapsing them the way GROUP BY does.
