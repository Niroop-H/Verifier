# Contributing to AEGIS EDA Verifier

Thank you for improving AEGIS EDA Verifier. Changes should make verification more reproducible, inspectable, and safe—not merely add a UI claim or a catalogue entry.

## Engineering rules

1. **Preserve existing behavior.** Extend the current `mqv_eda` package and public CLI contracts rather than introducing a competing implementation.
2. **Prove the behavior.** Add focused positive and negative tests for each new feature. Tests must check failure paths, invalid inputs, missing tools, and malformed artifacts where relevant.
3. **Make results auditable.** Record tool identity/version, input hashes, command outcomes, bounded logs, and explicit PASS/FAIL/BLOCKED/INCONCLUSIVE/NOT RUN/ERROR states where supported.
4. **Never turn missing evidence into PASS.** A check can pass only when that specific check actually ran and met its defined criteria.
5. **Keep hosted and local execution boundaries clear.** Vercel serves the web experience; native EDA tools run only in an explicitly configured execution environment. Do not imply a static page ran a simulator.
6. **Protect design data.** Bound uploads, archive extraction, execution time, output size, and path access. Do not log secrets or copy design inputs into evidence bundles unless the user explicitly opts in.
7. **Respect upstream licensing.** Pin third-party sources and preserve required copyright/license notices. Do not claim source is proprietary when it is third-party software.
8. **Document limitations.** Tool catalogue entries are not proof of a validated integration. No generic report establishes foundry sign-off or fabrication readiness.

## Before opening a pull request

- Run the relevant unit tests and source checks.
- Run EDA integration tests when the required tools are available; clearly report checks that could not run.
- Review generated reports and logs for sensitive data.
- Update user-facing documentation and the tool integration matrix.
- Keep changes focused and describe what was actually tested.

## Pull request checklist

- [ ] Behavior and acceptance criteria are described.
- [ ] Tests cover success and failure cases.
- [ ] Existing CLI/API behavior is preserved or migration is documented.
- [ ] Security, licensing, and data-handling implications are reviewed.
- [ ] Documentation distinguishes implemented, experimental, and planned features.
- [ ] No credentials, private design files, or unlicensed collateral are committed.
