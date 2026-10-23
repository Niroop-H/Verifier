# Isolated EDA job runner (deployment prototype)

## What this runner enforces

`scripts/run_isolated_job.sh` is a Docker wrapper for executing a single EDA command against a prepared worker image. It configures:

- No container network (`--network=none`) and no implicit image pull.
- Read-only container root filesystem; uploaded inputs mounted read-only.
- Only the designated output directory is mounted writable.
- Non-root numeric host identity; the wrapper refuses to run when the host caller is root.
- All Linux capabilities dropped and `no-new-privileges` enabled.
- Container memory, CPU, PID, file-size and open-file limits.
- A bounded, no-exec temporary filesystem.

Example:

```bash
chmod +x scripts/run_isolated_job.sh
scripts/run_isolated_job.sh mahquantum/mqv-worker:PINNED \
  ./job-input ./job-output -- \
  python3 -m mqv_eda verify /input/project --top top --out /output/report
```

The image must already exist locally. Replace the example image and command with an image built and reviewed for your deployment. Pin image references by digest in production. The example command is illustrative; confirm the worker image contains the required CLI, EDA tools and libraries.

## Important operational constraints

This is a **deployment prototype**, not a claim that a complete hosted worker or service is deployed. The wrapper must be exercised on the target Docker Engine and host OS before handling untrusted inputs.

- Run Docker on a patched, dedicated worker host. Prefer rootless Docker or an appropriately configured user namespace. Do not expose the Docker socket to the workload.
- Use an approved seccomp/AppArmor/SELinux policy and verify that the host kernel and Docker daemon enforce the requested limits.
- The output directory must be writable by the invoking non-root UID/GID. Treat all output as untrusted; validate and scan before exporting it.
- Do not mount customer secrets, home directories, PDK license credentials, host sockets or unrelated files into the container.
- The wrapper limits container memory to 4 GiB, CPU to 2 cores, PIDs to 128, file size to 1 GiB and `/tmp` to 1 GiB. Tune these values only through reviewed deployment changes and customer workload benchmarks.
- On termination, the wrapper traps TERM/INT/HUP and attempts to remove its daemon-managed container. The engine sends TERM first, allows a bounded cleanup grace period, then sends KILL to the process group. A SIGKILL, host failure or Docker daemon failure can bypass shell cleanup; production deployments need an external worker supervisor/reaper and must verify that no container survives a cancelled job.
- Container resource limits do not guarantee disk quota for the host output bind mount. Enforce a host filesystem/project quota for output and scratch storage.
- `--network=none` blocks container network interfaces, but host-side DNS, metadata, shared filesystems, runtime vulnerabilities and side channels still require separate review.
- Process termination, container escape resistance, cross-job isolation, output cleanup and quota behavior must be tested on the actual host. Never treat a wrapper script alone as a complete sandbox.

## Minimum acceptance tests before customer use

1. Run an approved benign RTL job and verify report export.
2. Attempt DNS/HTTP egress from inside the worker and verify it fails.
3. Attempt writes to the container root and input mount and verify they fail.
4. Exercise CPU, memory, PID, file-size, output-directory and temporary-directory limits.
5. Time out a parent process with descendants and confirm the job/container is fully terminated.
6. Attempt symlink/path traversal and cross-job file reads/writes.
7. Confirm that the worker has no host credentials, host sockets, cloud metadata access or unrelated mounts.
8. Retain logs, runtime configuration, image digest, tool versions and test results as deployment evidence.

## Not provided by this wrapper

It does not implement an upload/API service, authentication, tenant identity, queueing, per-tenant quotas, remote append-only audit storage, signing/SBOM generation, vulnerability response, or independent security review. Those remain separate Session 2 acceptance gates.
