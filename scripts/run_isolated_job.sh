#!/usr/bin/env bash
# Run one untrusted EDA job inside a constrained Docker container.
# Usage: run_isolated_job.sh IMAGE INPUT_DIR OUTPUT_DIR -- COMMAND [ARG...]
set -euo pipefail

usage() {
  echo "Usage: $0 IMAGE INPUT_DIR OUTPUT_DIR -- COMMAND [ARG...]" >&2
  exit 2
}

[[ $# -ge 5 ]] || usage
image="$1"
input_dir="$2"
output_dir="$3"
shift 3
[[ "$1" == "--" ]] || usage
shift
[[ $# -ge 1 ]] || usage

command -v docker >/dev/null 2>&1 || {
  echo "ERROR: Docker CLI is required." >&2
  exit 127
}
[[ -n "$image" ]] || usage
[[ -d "$input_dir" ]] || {
  echo "ERROR: input directory does not exist." >&2
  exit 2
}
mkdir -p -- "$output_dir"
input_dir="$(cd -- "$input_dir" && pwd -P)"
output_dir="$(cd -- "$output_dir" && pwd -P)"
worker_uid="$(id -u)"
worker_gid="$(id -g)"
if [[ "$worker_uid" -eq 0 ]]; then
  echo "ERROR: run this wrapper as a non-root host user." >&2
  exit 4
fi

# The image must already be present locally. Never pull an image as part of
# handling a customer job; image acquisition and signature/provenance checks
# belong to a separately controlled deployment pipeline.
if ! docker image inspect "$image" >/dev/null 2>&1; then
  echo "ERROR: worker image is not present locally: $image" >&2
  exit 3
fi

exec docker run --rm \
  --pull=never \
  --network=none \
  --read-only \
  --user="$worker_uid:$worker_gid" \
  --cap-drop=ALL \
  --security-opt=no-new-privileges:true \
  --pids-limit=128 \
  --memory=4g \
  --memory-swap=4g \
  --cpus=2 \
  --ulimit=fsize=1073741824:1073741824 \
  --ulimit=nofile=1024:1024 \
  --tmpfs=/tmp:rw,noexec,nosuid,nodev,size=1g,mode=1777 \
  --mount "type=bind,src=$input_dir,dst=/input,readonly" \
  --mount "type=bind,src=$output_dir,dst=/output" \
  --workdir=/output \
  "$image" "$@"
