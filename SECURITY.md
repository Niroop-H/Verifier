# Security Policy

AEGIS EDA Verifier is an engineering evaluation platform. A successful test run does not certify the security of a deployment or establish chip fabrication readiness.

## Reporting a vulnerability

Please do not publish exploit details, credentials, customer RTL, PDK collateral, or sensitive logs in a public issue. Contact the repository owner privately through GitHub's private vulnerability reporting feature, if enabled, or use a private contact channel already published by MAH Quantum. Include affected version/commit, impact, reproduction steps using non-sensitive examples, and any proposed mitigation.

Do not include secrets or confidential design data in the initial report.

## Safe use and deployment

- Treat RTL, testbenches, netlists, libraries, PDK files, logs, and reports as potentially confidential.
- Use only designs and collateral you are authorized to process.
- Do not upload export-controlled, classified, customer-confidential, or restricted IP to a public repository or an unapproved hosted service.
- Keep API tokens in deployment secret stores; never commit them or paste them into issues, logs, or chat.
- Run native EDA tools in a constrained worker with bounded CPU, memory, runtime, filesystem access, network access, and output size.
- Treat any worker isolation described in the repository as a prototype until deployment-specific tests demonstrate the controls.
- Review third-party tool and PDK licenses before redistribution or commercial use.

## Scope boundary

The project does not claim universal RTL correctness, formal completeness, foundry approval, regulatory authorization, or fabrication readiness. Verification claims must be limited to the checks actually executed and the evidence produced.
