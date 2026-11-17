---
type: reference
tags: [electronics]
---
# Raspberry Pi Pico Pinout

The pins I actually use.

## I2C

The default I2C bus uses GP4 for SDA and GP5 for SCL.

## Analog

There are three ADC inputs: GP26, GP27 and GP28. They read 0 to 3.3 V with 12-bit resolution.

## Power

- VSYS accepts 1.8 to 5.5 V.
- 3V3 OUT supplies up to about 300 mA to sensors.

## Warnings

The GPIO pins are not 5 V tolerant. Use a level shifter for 5 V sensors.
