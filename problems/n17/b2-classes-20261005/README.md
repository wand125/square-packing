# n17 sub-pattern certificates

Certificates for the n = 17 sub-pattern branch and bound of [jlevy/squares](https://github.com/jlevy/squares), hosted outside that repository as its operating rule OR-18 asks for bulk data. The certificate objects are release assets of this repository. Each directory here holds the hosted-data manifest entries (path, asset, size, SHA-256) for one release, and a summary of the run.

Context: jlevy/squares#358 (the two classes below) and jlevy/squares#367 (the branching rule).

## Release `b2-classes-20261005`

Two flagged classes of the 24-cell cover at cap `1169/250`, each proved certified-infeasible: no 17-square configuration of side at most the cap puts one centre in each listed cell.

| Class | Cells | Nodes | Closed leaves | Max depth | Objects | Bytes |
|---|---|---:|---:|---:|---:|---:|
| C1 | side-S0, side-N0, interior-SW, interior-NW, interior-W, interior-S, interior-SE | 194,328 | 97,563 | 39 | 391 | 287,584,492 |
| C2 | side-S0, side-W0, interior-SW, interior-NW, interior-W, interior-S, interior-SE | 79,396 | 40,224 | 32 | 161 | 112,191,343 |

- `b2-classes/manifest-C1.yaml`, `manifest-C2.yaml`: one entry per object (`path`, `asset`, `size`, `sha256`). The `path` is where the object goes in a jlevy/squares checkout.
- `b2-classes/C1-summary.json`, `C2-summary.json`: the producer's summary of each run (verdict, node and leaf counts, prune reasons, branch counts).

### How the trees were made

The producer is the pilot's sub-pattern branch and bound with the optional native kernel of jlevy/squares#350, with one change: the rule that chooses which square's angle to bisect ("B2", described in jlevy/squares#358 and #367). The judgement is unchanged. Every closure and every bound move passes the pilot's outward-rounded `dual_bound`, and the certificate format is the pilot's.

### Checks

| Class | Standing verifier `verify_n17_bb_certificate`, full mode, one process | Independent Rust checker, 4 threads |
|---|---|---|
| C1 | PASS, 5,906 s | PASS, 173 s |
| C2 | PASS, 2,220 s | PASS, 68 s |

All 552 objects were checked against the manifests (size and SHA-256) before upload.

### Fetching and checking

Download the assets of the release into the paths given by the manifest, for example with `gh release download b2-classes-20261005 --repo wand125/n17-certificates`, then move each file to its `path`. In a jlevy/squares checkout, from `packing/`:

```sh
python -m devtools.verify_n17_bb_certificate <certificate directory> --output receipt.json
```

## License

The certificates are data. They may be used freely; please cite jlevy/squares#358 when you do.
