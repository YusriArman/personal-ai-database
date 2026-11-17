---
type: project
tags: [robotics, club]
---
# Line Follower Robot

Club entry for the campus robotics competition on 22 April. Two DC motors, five infrared reflectance sensors across the front, and an Arduino Nano.

## Control

The robot steers with a PID loop. The values that finally stopped the wobble on the practice track were Kp 0.42, Ki 0.01 and Kd 0.18. Background on tuning is in [[PID Tuning Guide]].

## Problems

The motor driver overheats after about six minutes. I could not find its limits in [[Motor Driver Datasheet]] so we are adding a heat sink anyway.

- [ ] Add heat sink to the motor driver
- [x] Replace the front caster wheel
