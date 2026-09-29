# NCS E3 Family-2 Proof Obligation Ledger

Status: `SOURCE_ONLY`, `INDEPENDENT_BLIND_REVIEW_PASS`, `NOT_AUTHORIZED`.

| ID | Statement | Depends on | Required discharge | Current source |
| --- | --- | --- | --- | --- |
| D1 | `X_i(W)` row design matrix and coefficient spaces | Fixed node order, exact `W^2=WW` | Dimension and orientation stated | Factorization packet Sections 1--2 |
| D2 | `T^(2)_{W_0}` and `Q^G_{W_q}` | D1 | Direct-sum map definitions | Factorization packet Section 1 |
| D3 | Endpoint composition `Q^E=Psi circ R circ Q^G` | D2, fixed companion construction | `R` reshapes row-coordinate direct sums to operator tuples; `Psi` may be nonlinear; retained `G_1:p` projection makes deterministic endpoint factorization equivalent to linear operator factorization | Factorization packet Section 2 |
| L1 | Kernel factorization lemma | Linear maps only | Well-defined induced map on `im(T)` | Factorization packet Section 3 |
| T1 | Rowwise kernel-inclusion theorem | D2, L1 | Direct-sum kernel identity and both implications | Factorization packet Section 4 |
| C1 | Full-rank structured-positive corollary | T1 | `ker X_i={0}`, left inverse exists | Factorization packet Section 5 |
| F1 | One-hop negative fixture | Integer matrix multiplication | Equality at `P`, disagreement at `P^2` | Factorization packet Section 6 |
| F2 | Unrestricted second-order negative fixture | `P^3=I` | Equality at `P`, disagreement at `P^2` | Factorization packet Section 6 |
| F3 | Diagonal second-order negative fixture | Exact ranks and matrix products | Hidden `C_2` direction changes query | Factorization packet Section 6 |
| F4 | Diagonal structured-positive fixture | Exact determinants | Each row has rank three | Factorization packet Section 6 |
| F5 | Family non-equivalence witness | Fixed `(A,B)` over `{0,V,2V}` | Derive contradiction `2I != 4I` | Factorization packet Section 6 |

Dependency DAG: `D1 -> D2 -> {D3,L1} -> T1 -> C1`; fixtures F1--F5 are
independent exact checks that constrain the theorem's interpretation. There
are no probability limits, stochastic modes, asymptotic constants or measure
interchanges in this packet.

Blind-review gate: a fresh read-only reviewer must check every D/L/T/C/F item,
including `N=1`, rank-deficient and endpoint-projection counterexamples. A
review result is usable only through a machine-readable `PASS` receipt with no
open findings that binds the exact proof-packet SHA-256. Such a receipt does
not make the packet `CANDIDATE_READY`, does not authorize science, and does
not change any controlling audit verdict.

Blind-review result: `NCS_E3_FAMILY2_PROOF_BLIND_REVIEW_RECEIPT.json` records
`PASS`, no open findings, and the exact proof-packet SHA-256. It validates the
formal representation statement only; the eight artifact lifecycle states
remain `SOURCE_ONLY` and production preflight remains closed.
