"""Detached evidence bundle signatures using the OpenSSL CLI.

Private keys must be held and managed by the customer or release operator.
This module never embeds a private key in a bundle. Signature validity depends
on trusting the public key supplied to verification.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

def sign_bundle(bundle: Path, private_key: Path, signature: Path, *, openssl: str = "openssl") -> dict[str, str]:
    bundle, private_key, signature = Path(bundle), Path(private_key), Path(signature)
    if not bundle.is_file():
        raise ValueError(f"Bundle does not exist: {bundle}")
    if not private_key.is_file():
        raise ValueError(f"Private key does not exist: {private_key}")
    exe = shutil.which(openssl)
    if not exe:
        raise ValueError("OpenSSL executable is unavailable")
    signature.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([exe, "dgst", "-sha256", "-sign", str(private_key),
                           "-out", str(signature), str(bundle)],
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=30, check=False)
    if proc.returncode != 0 or not signature.is_file():
        raise ValueError("OpenSSL signing failed: " + proc.stderr.decode("utf-8", "replace")[-2000:])
    return {"bundle_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
            "signature": str(signature), "signature_sha256": hashlib.sha256(signature.read_bytes()).hexdigest(),
            "algorithm": "OpenSSL dgst -sha256 (key algorithm determined by supplied private key)"}

def verify_bundle_signature(bundle: Path, public_key: Path, signature: Path, *, openssl: str = "openssl") -> dict[str, str | bool]:
    bundle, public_key, signature = Path(bundle), Path(public_key), Path(signature)
    for path, label in ((bundle, "Bundle"), (public_key, "Public key"), (signature, "Signature")):
        if not path.is_file():
            raise ValueError(f"{label} does not exist: {path}")
    exe = shutil.which(openssl)
    if not exe:
        raise ValueError("OpenSSL executable is unavailable")
    proc = subprocess.run([exe, "dgst", "-sha256", "-verify", str(public_key),
                           "-signature", str(signature), str(bundle)],
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=30, check=False)
    valid = proc.returncode == 0 and b"Verified OK" in proc.stdout
    return {"valid": valid, "bundle_sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
            "signature_sha256": hashlib.sha256(signature.read_bytes()).hexdigest(),
            "message": (proc.stdout + proc.stderr).decode("utf-8", "replace")[-2000:],
            "trust_note": "A valid signature proves the matching private key signed these bytes only if the public key identity is independently trusted."}
