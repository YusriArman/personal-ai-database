---
type: reference
tags: [robotics, control]
---
# PID Tuning Guide

A PID controller corrects an error using three terms.

## The terms

- Proportional reacts to the current error. Too high and the system oscillates.
- Integral reacts to accumulated error and removes steady offset. Too high and it overshoots.
- Derivative reacts to the rate of change and damps oscillation. It amplifies sensor noise.

## Ziegler–Nichols method

Set Ki and Kd to zero. Raise Kp until the output oscillates steadily; that gain is Ku and the period is Tu. Then use Kp = 0.6 Ku, Ki = 1.2 Ku / Tu and Kd = 0.075 Ku Tu.

## Manual tuning

Raise Kp until it wobbles, add Kd until the wobble stops, then add a little Ki.
