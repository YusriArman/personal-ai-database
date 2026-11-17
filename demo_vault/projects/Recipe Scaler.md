---
type: project
tags: [web, cooking]
---
# Recipe Scaler

A one-page web tool: paste a recipe, choose how many servings, and it rescales every quantity. Plain JavaScript, no framework.

## Known bug

Tablespoons are converted to millilitres using 20 ml, which is the Australian tablespoon. It should be 15 ml. Small recipes come out fine but a scaled-up curry was far too salty.

## Ideas

Rounding to sensible kitchen amounts, for example 1/3 cup instead of 0.31 cup.
