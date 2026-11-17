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
   TUNE_1 LEVEL_1   OSC1 ─┐             │
   TUNE_2 LEVEL_2   OSC2 ─┼─ mixer U2C ─ clip U2D ─ Sallen-Key U3A ─ buffer U3B ─ MASTER_LEVEL ─ J2 3.5 mm
   TUNE_3 LEVEL_3   OSC3 ─┘                LED pair       CUTOFF1    RES1           A10k
                                        D2/D3 via R32
                                        to VREF
```

## Key specs

| Spec | Value |
| --- | --- |
| Supply | USB-C VBUS 5 V via 6-pin 2.54 mm breakout (polyfuse + ferrite) |
| Virtual ground | VREF = 2.5 V (R2/R3 divider, buffered by U3C) |
| Oscillators | 3× op-amp saw core (integrator + comparator + BC547 cap reset) |
| Osc range | ~0–1.5 kHz (4.7 k Rin), parks at 0 Hz at the low end of TUNE |
| Mixer | Inverting summer, unity gain per osc (10 k/10 k) |
| Clip | Shunt LED clipper on U2D out: anti-parallel red LEDs + 220 Ω to VREF |
| Filter | 2-pole Sallen-Key LP, ~72 Hz–7.2 kHz cutoff (dual-gang 100k + 1 k min), RES to self-oscillation |
| RES limit | Anti-parallel yellow LEDs across RES1: oscillation settles ~±2 V clean sine |
| Output | AC-coupled 10 µF → A10k master level → 1 k series R to tip+ring, sleeve = GND |
| Test points | TP1 +5V, TP2 VREF, TP3–5 SAW1–3, TP6 MIX, TP7 CLIP, TP8 OUT, TP9 GND |

## Controls (9 pots)

- **TUNE_1/2/3** — B10k, oscillator pitch (current into the integrator)
- **LEVEL_1/2/3** — B10k, per-osc level into the mixer
- **CUTOFF1** — dual-gang 100k, tracks both filter sections
- **RES1** — B22k, filter feedback; self-oscillation over the top half
  (yellow LEDs light when the filter sings)
- **MASTER_LEVEL1** — A10k (audio taper), output volume after the DC-block cap

## Design notes

- **Op-amps**: 3× MCP6004-I/P (DIP-14), chosen because TL07x cannot run on
  a single 5 V rail (its input common-mode range doesn't include ground).
  MCP6004 is rail-to-rail I/O and cheap/common.
- **Saw core**: tune pot feeds current through R_in (4.7 k) into the
  integrator summing node; the comparator trips at ~0.9 V (R5/R6 divider)
  and pulses the BC547 base, discharging the integrator cap (E→SAW,
  C→summation).
- **Clip**: U2D is a ×2 inverting stage (R24/R23); its output feeds an
  anti-parallel red LED pair through R32 (220 Ω) to VREF. When the signal
  exceeds ~±Vf (~1.9 V red) around VREF, the LEDs squash the peak and
  visibly blink — a shunt clipper referenced to the virtual ground,
  *not* to GND.
- **Filter Q**: RES1 (B22k) varies feedback against R28 (4.7 k) at
  U3A −in: gain range ≈ 1→5.7, so Q crosses self-oscillation at ~40 %
  of travel — the top of the pot is an oscillator whose pitch follows
  CUTOFF1.
- **RES limiter**: an anti-parallel yellow LED pair sits in parallel
  with RES1's feedback path. Below ~±2 V they are transparent; past the
  self-oscillation threshold they collapse the feedback gain, so the
  loop settles into a clean ~±2 V sine instead of slamming the op-amp
  rails. Yellow lit = filter oscillating, red lit = signal clipping —
  classic amplitude stabilization, and a nice live readout.
- **LED choice**: only low-Vf colors work here — the op-amp can only
  swing ~±2 V around VREF, so blue/white/true-green (~3 V) would never
  conduct. Red for the clipper (lowest threshold), yellow for RES.
- All resistors 1 %, all caps TH ceramic (100 n/22 n) or electrolytic
  (1 µ/10 µ/100 µ).

## Files

```
kicad/edu-01.kicad_pro   project
kicad/edu-01.kicad_sch   schematic
kicad/edu-01.kicad_pcb   board layout
```

## BOM (core parts)

| Qty | Part |
| --- | --- |
| 3 | MCP6004-I/P (DIP-14) |
| 3 | BC547 (TO-92) |
| 5 | LED (1 × power, 2 × red clip pair, 2 × yellow RES pair) |
| 6 | B10k 9 mm vertical pot (Alpha RD901F-style) |
| 1 | A10k 9 mm vertical pot (master level) |
| 1 | dual-gang 100k pot (RD902F-style) |
| 1 | B22k 9 mm pot |
| 31 | resistors 1 % (0.25 W, axial): 10×10k, 7×4.7k, 3×47k, 3×1M, 4×1k, 1×20k, 1×100k, 1×1.5k, 1×220 |
| 16 | ceramic + electrolytic caps (TH) |
| 1 | USB-C 6-pin 2.54 mm breakout |
| 1 | polyfuse 500 mA, ferrite bead, SJ1-3533NG 3.5 mm jack |

## Build notes

- J1 pinout used: **1 = VBUS, 2 = GND**; pins 3–6 are NC on the board.
- **CC resistors**: for a USB-C host/charger to deliver power, both
  CC1 and CC2 must each see **5.1 kΩ to GND** (Rd). Check your
  breakout's silkscreen — many 6-pin boards already have them fitted;
  if not, add one 5.1 kΩ from each CC pin to GND. Never share a single
  resistor between CC1/CC2, and don't duplicate on-board if the
  breakout has them (parallel → ~2.55 kΩ → source refuses power).
- Transistor pinout: **BC547 is C-B-E** — check the silkscreen before
  soldering.
- U3D is a spare op-amp wired as a VREF follower (keep it populated).
- Probe order for a first smoke test: TP1 (+5 V) → TP2 (VREF ≈ 2.5 V) →
  TP3–5 (saws) → TP6 (mix) → TP7 (clip) → TP8 (out).
