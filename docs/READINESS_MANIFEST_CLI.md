# Readiness manifest CLI

MQV can evaluate a **declared scope** against a caller-supplied evidence inventory. This is a policy check, not independent evidence authentication and not chip/foundry sign-off.

Run from the repository root:

```bash
python -m mqv_eda.readiness_cli examples/readiness-manifest.json --out readiness-assessment.json
```

The command returns exit code 0 only when all declared evidence records pass the policy and include a reviewer. It returns 1 for a valid but incomplete, blocked, failed, or review-required assessment, and 2 for an invalid manifest or I/O error. The JSON assessment always contains `"fabrication_ready": false`.

## Manifest schema

- `scope`: non-empty string describing exactly what is being assessed.
- `required_units`: non-empty list of IDs from `mqv_eda/verification_catalog.py`.
- `evidence`: list of records with `unit_id`, `status`, and optional `evidence_uri`, `input_digest`, `tool_version`, `reviewed_by`.
- Status values must match MQV's status enum: `PASS`, `FAIL`, `BLOCKED`, `INCONCLUSIVE`, `NOT RUN`, or `ERROR`.

Example (illustrative paths and digest only):

```json
{
  "scope": "Pilot RTL lint for project alpha, source revision 0123456789abcdef",
  "required_units": ["RTL_LINT"],
  "evidence": [
    {
      "unit_id": "RTL_LINT",
      "status": "PASS",
      "evidence_uri": "artifacts/lint/console.log",
      "input_digest": "sha256:replace-with-real-input-digest",
      "tool_version": "replace-with-real-tool-version",
      "reviewed_by": "reviewer-id"
    }
  ]
}
```

## Safety and limitations

- The command does not run the checks listed in the manifest. A `PASS` is an assertion in the supplied manifest, not proof that a tool ran.
- Evidence URIs are not fetched; artifact contents, digests, tool versions and reviewer identities are not authenticated.
- Duplicate records for a required unit are treated as ambiguous/missing by the policy evaluator.
- Units not included in `required_units` are outside the declared assessment scope.
- A complete manifest can only produce `EVIDENCE COMPLETE — SIGN-OFF STILL REQUIRED`. It can never establish fabrication readiness.
- Do not use illustrative example values as real verification evidence.
