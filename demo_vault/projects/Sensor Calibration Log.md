---
type: project
tags: [electronics]
---
# Sensor Calibration Log

Raw numbers for the [[Greenhouse Monitor]] probes.

## Soil probe

The capacitive probe reads about 520 in dry air and about 260 in a glass of water. I map that range to 0–100 percent. Anything under 35 percent means the basil needs watering.

## Temperature

The DHT22 reads 0.8 °C higher than the lab thermometer, so the firmware subtracts 0.8 before logging.

## Notes

Readings drift when the probe cable runs next to the pump wire. Keeping them 5 cm apart fixed it.
