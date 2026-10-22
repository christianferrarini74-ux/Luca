# IRIS-17 controlled manual — revision 1.0

[Italian operational document](it/esperimenti/iris17-manuale.md).
Fictional test device: never use these specifications on real equipment.
This English translation is documentation, not additional model input.

## Index

1. Modes and startup
2. Sensor and thresholds
3. E42 alarm
4. Recovery
5. Maintenance
6. Missing specifications

## 1. Modes and startup

IRIS-17 has two modes: OSSERVA and IRRIGA. Startup always selects OSSERVA:
humidity is measured but the valve stays closed. AVVIA selects IRRIGA only
when no alarm is active. Opening in IRRIGA follows chapter 2. For active E42,
consult chapters 3 and 4.

## 2. Sensor and thresholds

U7 measures soil humidity every 30 seconds. In IRRIGA, with the valve closed
and no active alarm, three consecutive readings strictly below 28% open the
valve. A reading at or above 28% resets this count. With the valve open, a
reading at or above 41% closes it. OSSERVA keeps it closed. Invalid samples
follow chapter 3.

## 3. E42 alarm

Two consecutive invalid U7 samples trigger E42. A valid sample before the
second invalid one resets the error count. E42 immediately closes the valve
and selects OSSERVA. A low but valid humidity reading is not an invalid sample.
Signal recovery alone does not clear E42. See recovery in chapter 4 and
maintenance in chapter 5.

## 4. Recovery

After E42, inspect the U7 connection; disconnect power before working on
connections. After inspection and power-up, four consecutive valid samples
and then CONFERMA are required to clear E42. An invalid sample interrupts
the four-sample sequence. Power cycling alone does not clear the stored alarm.
CONFERMA without the four valid samples cannot clear it. After clearance,
the mode remains OSSERVA: AVVIA is required to return to IRRIGA. Valve opening
then requires the conditions in chapter 2.

## 5. Maintenance

Every 14 days, clean U7 with a dry cloth and inspect its connection.
Disconnect power before maintenance. Do not immerse the controller. If E42
persists after inspection and chapter 4 recovery, contact technical service;
the manual prescribes no other repairs.

## 6. Missing specifications

Supply voltage, valve flow rate, Wi-Fi support and maximum irrigation duration
are unspecified. Humidity thresholds do not determine them. These procedures
apply only to fictional IRIS-17 revision 1.0.
