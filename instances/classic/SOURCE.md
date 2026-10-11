# Classic Orienteering Problem benchmarks (visit time v = 0)

Downloaded on 2026-10-11 from the KU Leuven CIB Orienteering Problem page:
https://www.mech.kuleuven.be/en/cib/op

| Folder          | Download URL                                                       | Files | Points |
|-----------------|--------------------------------------------------------------------|-------|--------|
| TsiligiridesOP1 | https://www.mech.kuleuven.be/en/mim/op/instances/TsiligiridesOP1   | 18    | 32     |
| TsiligiridesOP2 | https://www.mech.kuleuven.be/en/mim/op/instances/TsiligiridesOP2   | 11    | 21     |
| TsiligiridesOP3 | https://www.mech.kuleuven.be/en/mim/op/instances/TsiligiridesOP3   | 20    | 33     |
| ChaoOP64        | https://www.mech.kuleuven.be/en/mim/op/instances/ChaoOP64          | 14    | 64     |
| ChaoOP66        | https://www.mech.kuleuven.be/en/mim/op/instances/ChaoOP66          | 26    | 66     |

Files are unchanged from the archives. The format description
(`OP_format.txt`) is from https://www.mech.kuleuven.be/en/mim/op/instances/OP_format:
first line `Tmax P`, then `x y S` per point; the first point is the start,
the second point is the end; Euclidean distances.

## File format and distance convention

- Plain text, tab separated, CRLF line endings. Line 1: `Tmax P` (P = 1 path).
  Then one line per point: `x y S` (coordinates and score, no visit time).
- The first point is the start, the second point is the end; both have score 0.
  All files of one set contain the same points and differ only in Tmax.
- Distances: Euclidean, not rounded (real-valued), as stated in `OP_format.txt`.
  The reference paper below does not state its convention, so it was checked
  empirically (`results/distance_convention/README.md`): with unrounded distances
  our SA reaches all 89 reference values and never exceeds one, while rounding to
  the nearest integer, floor and ceil each contradict the references (scores above
  them, or far below on instances where unrounded distances reach them).
- TsiligiridesOP1 is the ORIGINAL set 1: it contains the point (4.9, 18.9).
  Some papers also use a corrected version (point moved to (4.9, 14.9), called
  "set 4" in the reference paper); its values differ (e.g. Tmax 75: 275 vs 270)
  and must not be used for these files.

## Reference values (`references.csv`)

All 89 values come from ONE source:

> K. Szwarc, U. Boryczka (2022). A novel approach to the Orienteering Problem based
> on the Harmony Search algorithm. PLoS ONE 17(2): e0264584.
> https://doi.org/10.1371/journal.pone.0264584 (open access)

Column "Best" of Table 1 (Tsiligirides set 1, original), Table 2 (set 2),
Table 3 (set 3), Table 5 (Chao 64) and Table 6 (Chao 66). The paper defines "Best"
as the best objective value reported in the literature it reviews (GA, GLS, ACO,
VNS, GRASP, GSOA, EA4OP, ...), so every value is labelled `best-known` (no proof of
optimality is claimed there). Transcription was checked against the column averages
printed in the paper. The p64/p66 values agree with Campos et al. (2014),
JORS 65(12), Tables 4 and 6. Page numbers in the paper: Tables 1-2 on p. 12,
Tables 3-4 on p. 13, Tables 5-6 on p. 14 (of 21).

## Instances used in the experiments (`selection.csv`)

17 of the 89 instances (approved): per set the Tmax values whose reference collects
about 25 %, 50 % and 75 % of the total score, plus one instance per Chao set that
published heuristics found hard (Chao 64 Tmax 55, Chao 66 Tmax 110). All 89
reference values stay in `references.csv`.

Original publications:
- T. Tsiligirides (1984). Heuristic methods applied to orienteering.
  Journal of the Operational Research Society 35(9), 797-809.
- I-M. Chao, B. L. Golden, E. A. Wasil (1996). A fast and effective heuristic
  for the orienteering problem. European Journal of Operational Research 88(3), 475-489.
