---
type: project
tags: [rust, productivity]
---
# Study Timer CLI

A terminal pomodoro timer written in Rust as a way to learn the language. It runs 25 minutes of work followed by a 5 minute break, with a longer 20 minute break after four rounds.

## What I learned

Ownership made sense once I stopped fighting the borrow checker and passed references instead of cloning everything. The clap crate handles the command line arguments.

## Later

It would be nice to log finished sessions to a file so I can see how much I studied each week.
