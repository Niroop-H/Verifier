# Evidence manifest and integrity checks

Every `mqv-eda verify` run writes an `evidence-manifest.json` alongside `report.json` and `report.html`. The manifest records each check's status, required/optional flag, message, exit code, tool version, duration, known input hashes, and captured log digest/size when available.

## Verify a saved manifest

```bash
python -m mqv_eda verify-evidence build/demo/evidence-manifest.json
```

Exit codes are `0` when referenced evidence files match, `1` when an integrity problem is detected, and `2` when the manifest cannot be read or verified. Reports contain relative paths for files inside the evidence directory. Inputs outside that directory are shown by basename to avoid disclosing machine-specific absolute paths.

## Interpretation and limitations

- The manifest records both the digest captured by the check (when supplied by the engine) and the observed digest at manifest generation time. A difference between these fields can indicate that an input changed during the run.
- Integrity verification only opens files whose resolved paths remain within the manifest directory; unsafe paths are rejected.
- Missing or unreadable files and hash mismatches fail integrity verification.
- A green integrity result means only that the referenced files matched the hashes recorded in this manifest. It does not prove the manifest itself is authentic, that the execution host or tools were trusted, that tests were complete, that the RTL is correct, or that a design is ready for fabrication.
- For evidence exchange, package the manifest and every referenced file in a stable directory layout. Keep signed attestations and independently controlled, append-only storage as separate future controls; this feature is not a digital signature.

The manifest is a first step toward repeatable customer evaluation and audit-friendly engineering evidence. It must not be described as an independent audit or certification.
