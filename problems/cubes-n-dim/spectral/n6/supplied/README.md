# Unrestricted dimension-six proof bundle — VERIFIED

The main theorem in this bundle is unrestricted Lemma F for every orthogonal six-by-six matrix, with the consequence that the minimum enclosing cube side for two unit six-cubes is 2. It has no lower-dimensional packing premise.

**The proof is complete.** The cap and strip have each passed two exact implementations, and the C5 near-axis theorem has passed independent mathematical audit and standalone rational saved-tree replay. All checker implementations and terminal receipts are included.

Start with [PROOF.md](d6_proof_handoff/PROOF.md). The proof uses three overlapping regions:

- Maximum squared coordinate at most 13/20: central-cap exact certificate.
- Maximum squared coordinate from 13/20 to 159/200: verified strip certificate.
- Maximum squared coordinate at least 141/200: unrestricted C5 quadratic-minorant argument.

The [C5 dependency graph](general_dimension/c5_dependency_graph.md) explains why neither the dimension-four nor the dimension-five packing result is needed. The positive C5 certificate includes all lower-rank positive cases by zero padding; sign lifting supplies arbitrary signs.

## Reproduce the exact checks

Use Python 3. All commands below use only its standard library. Run from the bundle root. Numerical witness generation is unnecessary for verification.

Central cap, two exact implementations:

```sh
(cd d6_spectral/certificate_cap65 && python replay.py)
(cd d6_spectral/certificate_cap65 && python independent_verify.py certificate.json)
```

Strip, two exact implementations:

```sh
(cd d6_spectral/certificate_cap795 && python replay.py)
(cd d6_strip_independent && python verify.py ../d6_spectral/certificate_cap795/certificate.json)
```

C5 saved-tree certificate, standalone exact checker:

```sh
python general_dimension/replay_positive_c5_exact_tree.py
```

Additional small exact checks:

```sh
python d6_central/replay_exterior.py
python d6_central/replay_joint.py
python d6_exterior_audit/projected_audit.py
```

The C5 generator and its independently implemented allocation/coverage audit are also included for optional reproduction. That audit uses floating proposals only to choose rational witnesses; every acceptance is independently exact. The saved-tree checker above uses no floating arithmetic or producer imports at all.

## Certificate identity and evidence

- Cap raw SHA-256: `c33aa40033275bf66488a8b781898dcb051aad39459caa6900e0d30413986b82`.
- Strip raw SHA-256: `0bd2317bd8c2fdc87ec9d2350ee6f136680d74430511aa70ca10467862fee149`.
- C5 compressed tree SHA-256: `12c4704d887eccc01d879935e495c3532fbe794a5c022255c8e40cb3d599d56d`.

Results and mathematical audits are beside their corresponding code. The strip has 4,001,519 records, 2,000,762 leaves and 59,961 vertices; both exact replays passed with matching counts and exact slack. Informational timing values never enter acceptance decisions.

`STATUS.json` records completion state. `SHA256SUMS` lists file hashes. All proof references stay within this bundle except the cited published concavity theorem. No cloud service or network access is required to run the checks.
