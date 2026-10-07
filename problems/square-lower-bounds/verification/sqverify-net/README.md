# Fine-net adaptation of sqverify_fast

This is a copy of Joshua Levy / the squares project's independent Rust verifier,
https://github.com/jlevy/squares, at the revision in UPSTREAM_COMMIT, with
format-M admission adapted to read the candidate's declared uniform proof_net
(step and last) instead of assuming the old 201-direction net. This is the
same local checker used for the earlier mixed_n18_L470 report. No upstream PR
or acceptance of this adaptation is claimed here. Attribution and licenses
are in UPSTREAM_LICENSE; the original independence records are included.

The source digest embedded in the recorded runs is
`ab6e33e164dbc5c32b40349ba55981b58e630b5eef59534196a69d259404fd7c`.
It is computed from Cargo.toml, Cargo.lock, build.rs and sorted src/*.rs, as
specified in build.rs. These files reproduce that digest exactly.

Build with Rust 1.98 and the locked dependencies:

```sh
cargo build --release --locked
```

From the repository root (replace the certificate and rational side as needed):

```sh
gzip -c certificates/mixed_n18_L4704/candidate.json > /tmp/n18-candidate.json.gz
verification/sqverify-net/target/release/sqverify-fast --candidate /tmp/n18-candidate.json.gz --n 18 --side 588/125 --directions all --threads 1 --confirm
```

For n19 use mixed_n19_L48229, --n 19 and --side 48229/10000.
The independent checker operates on the rational measure, not the generating
checker's direction receipts. Recorded JSONL outputs are under each
certificate's verification directory. This publication audit did not rebuild
the binary or rerun the crate's whole test suite; source/build digest identity
and the actual certificate/control results are recorded separately.

The exact gzip input bytes of each recorded run are also retained as
`verification/independent-input.json.gz` in the certificate directory. The
receipt input_sha256 hashes those compressed bytes; after decompression the
content equals the public candidate.json byte for byte. Recompressing the same
candidate can change the gzip hash without changing its rational contents.
