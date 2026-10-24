# Evidence manifest and integrity checks

Every `mqv-eda verify` run writes an `evidence-manifest.json` alongside `report.json` and `report.html`. The manifest records each check's status, required/optional flag, message, start timestamp, exit code, tool version, duration, known input hashes, a redacted command, a SHA-256 fingerprint of the exact command arguments, and captured log digest/size when available. Absolute command paths are reduced to relative paths within the bundle or basenames for external files.

## Create a portable evidence bundle

By default, MAH Quantum Verify does **not** copy input files that are outside the selected output directory. RTL, netlists, timing libraries, PDK collateral and rule decks can be confidential or licence-restricted. External inputs are listed by basename and marked `bundled: false`; the integrity verifier refuses to claim that those files have been re-verified from the bundle.

When you are explicitly authorized to duplicate the design collateral, use the opt-in flag:

```bash
python -m mqv_eda verify fixtures/projects/good --top comb \
  --testbench tb_comb.v --sim-top tb_comb --out build/demo --bundle-inputs
python -m mqv_eda verify-evidence build/demo/evidence-manifest.json
```

`--bundle-inputs` copies the known external input files into `build/demo/evidence-inputs/` using digest-based filenames. The default total input-copy limit is 100 MiB; adjust it with `--max-bundle-mb N`. The size limit is checked before copying begins. Bundling may duplicate confidential design IP or licensed collateral, so use it only when you have permission to retain and distribute those files. The output folder should be handled as sensitive engineering data.

## Verify a saved manifest

```bash
python -m mqv_eda verify-evidence build/demo/evidence-manifest.json
```

Exit codes are `0` when all referenced evidence is present and matches, `1` when an integrity problem is detected, and `2` when the manifest cannot be read or verified. The verifier resolves artifact references and rejects paths that escape the manifest directory.

## Interpretation and limitations

- The manifest records both the digest captured by the check and the observed digest at manifest generation time when the source remains available. Differences indicate that the source may have changed during the run and cause integrity verification to fail.
- Missing or unreadable files, unsafe paths, hash mismatches and external unbundled inputs prevent an overall integrity PASS.
- The command fingerprint lets reviewers compare exact command arguments without disclosing host-specific absolute paths in the manifest. The redacted command is for human review and may not be directly executable as written. A fingerprint is not a signature or proof that the command was actually executed.
- A green integrity result means only that the bundled referenced files matched the hashes recorded in the manifest. It does not prove the manifest itself is authentic, that the execution host or tools were trusted, that tests were complete, that the RTL is correct, or that a design is ready for fabrication.
- For evidence exchange, package the manifest and every referenced file in a stable directory layout. Keep signed attestations and independently controlled, append-only storage as separate future controls; this feature is not a digital signature.

The manifest is a first step toward repeatable customer evaluation and audit-friendly engineering evidence. It must not be described as an independent audit or certification.
