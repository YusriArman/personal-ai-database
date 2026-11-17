---
type: project
tags: [python]
---
# Reading Tracker Script

A Python script that reads the "My Clippings" file from my Kindle and turns the highlights into one markdown file per book.

## How it works

It splits the file on the separator line, groups highlights by book title and sorts them by location. Duplicate highlights are dropped by comparing the first 40 characters.

## Limits

It breaks on books with a colon in the title because I used the colon as a delimiter. That bug is still there.
