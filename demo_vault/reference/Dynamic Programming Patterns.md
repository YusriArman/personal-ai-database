---
type: reference
tags: [algorithms]
---
# Dynamic Programming Patterns

Dynamic programming solves a problem by combining answers to overlapping subproblems.

## Two styles

- Memoization is top-down: write the recursion, then cache each result.
- Tabulation is bottom-up: fill a table from the smallest subproblem upward.

## Common patterns

- Knapsack: choose items under a weight limit. State is (item index, remaining capacity).
- Longest increasing subsequence: state is the best length ending at each position.
- Coin change: state is the amount. Greedy fails when denominations are irregular.

## Checklist

Define the state, write the recurrence, set the base cases, decide the order of filling.
