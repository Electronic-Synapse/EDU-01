# EDU-01 — Analog Drone Synth (educational kit)

Three saw-core VCOs mixed, soft-clipped and run through a resonant
low-pass filter. Everything on a single +5 V USB-C supply, built only
from common **through-hole** parts — meant to be built on a real PCB,
probed at every stage, and used to teach analog synth fundamentals.

```
USB-C 6-pin breakout ─ F1 polyfuse ─ L1 ferrite ─ +5V
                                        │
                              R2/R3 divider + U3C buffer = VREF (2.5 V)
                                        │
   TUNE1 LEVEL1     OSC1 ─┐             │
   TUNE2 LEVEL2     OSC2 ─┼─ mixer U2C ─ clipper U2D ─ Sallen-Key U3A ─ buffer U3B ─ J2 3.5 mm
   TUNE3 LEVEL3     OSC3 ─┘                D2/D3       CUTOFF (RV7A/B) RES (RV8)
```

## Key specs

| Spec | Value |
|---|---|
| Supply | USB-C VBUS 5 V via 6-pin 2.54 mm breakout (polyfuse + ferrite) |
| Virtual ground | VREF = 2.5 V (R2/R3 divider, buffered by U3C) |
| Oscillators | 3× op-amp saw core (integrator + comparator + 2N3904 cap reset) |
| Osc range | ~0–2 kHz, parks at 0 Hz at the low end of TUNE |
| Mixer | Inverting summer, ~unity gain per osc (22 k/22 k) |
| Soft clip | 1N4148 anti-parallel pair + R25 in feedback of U2D |
| Filter | 2-pole Sallen-Key LP, ~720 Hz–7.2 kHz cutoff (dual-gang B100k + 1 k min), RES to self-oscillation |
| Output | AC-coupled 10 µF, 1 k series R to tip+ring, sleeve = GND |
| Test points | TP1 +5V, TP2 VREF, TP3–5 SAW1–3, TP6 MIX, TP7 CLIP, TP8 OUT, TP9 GND |

## Controls (8 pots)

- **TUNE1/2/3** — B10k, oscillator pitch (current into the integrator)
- **LEVEL1/2/3** — B10k, per-osc level into the mixer
- **CUTOFF** — dual-gang B100k (RV7A/RV7B), tracks both filter sections
- **RESONANCE** — B22k, filter feedback; max ≈ self-oscillation

## Design notes

- **Op-amps**: 3× MCP6004-I/P (DIP-14), chosen because TL07x cannot run on
  a single 5 V rail (its input common-mode range doesn't include ground).
  MCP6004 is rail-to-rail I/O and cheap/common.
- **Saw core**: tune pot feeds current through R_in into the integrator
  summing node; the comparator trips at ~0.9 V (R5/R6 divider) and pulses
  the 2N3904 base, discharging the integrator cap (E→SAW, C→summation).
- **Soft clip**: separate inverting stage after the mixer so it can be
  probed/bypassed; diodes begin conducting ~0.55 V around the 20 k path.
- **Filter Q**: RES pot varies negative feedback into U3A −in against
  the R28 VREF bias; gain range ≈ 1→3.2, reaching self-oscillation.
- All resistors 1 %, all caps TH ceramic (100 n/22 n) or electrolytic
  (1 µ/10 µ/100 µ).

## Files

```
kicad/edu-01.kicad_pro   project
kicad/edu-01.kicad_sch   schematic (generated)
kicad/edu-01.kicad_pcb   skeleton board (2-layer, 100×60 mm outline)
kicad/gen_schematic.py   schematic/PCB generator (see below)
kicad/gen/sym/*.sym      symbol blocks extracted from stock KiCad 10 libs
```

## Regenerating the schematic

The schematic is authored programmatically (grid-snapped, pin-derived
wiring). To regenerate after edits:

```sh
cd kicad && python3 gen_schematic.py
kicad-cli sch erc edu-01.kicad_sch        # expect 0 violations
kicad-cli sch export pdf edu-01.kicad_sch -o edu-01.pdf
```

## BOM (core parts)

| Qty | Part |
|---|---|
| 3 | MCP6004-I/P (DIP-14) |
| 3 | 2N3904 (TO-92) |
| 2 | 1N4148 |
| 1 | 3 mm LED |
| 6 | B10k 9 mm vertical pot (Alpha RD901F-style) |
| 1 | dual-gang B100k (RD902F-style) |
| 1 | B22k 9 mm pot |
| 31 | resistors 1 % (0.25 W, axial) |
| 16 | ceramic + electrolytic caps (TH) |
| 1 | USB-C 6-pin 2.54 mm breakout |
| 1 | polyfuse 500 mA, ferrite bead, SJ1-3533NG 3.5 mm jack |

## Build notes

- J1 pinout used: **1 = VBUS, 2 = GND**; pins 3–6 (D±/CC) are NC.
- U3D is a spare op-amp wired as a VREF follower (keep it populated).
- Probe order for a first smoke test: TP1 (+5 V) → TP2 (VREF ≈ 2.5 V) →
  TP3–5 (saws) → TP6 (mix) → TP7 (clip) → TP8 (out).
