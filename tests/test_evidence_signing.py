from pathlib import Path
import shutil
import subprocess
import pytest
from mqv_eda.evidence_signing import sign_bundle, verify_bundle_signature

@pytest.mark.skipif(not shutil.which("openssl"), reason="OpenSSL CLI not installed")
def test_detached_signature_valid_and_tamper_detected(tmp_path):
    bundle=tmp_path/"evidence.zip"; bundle.write_bytes(b"test evidence")
    private=tmp_path/"private.pem"; public=tmp_path/"public.pem"
    subprocess.run(["openssl","genpkey","-algorithm","RSA","-pkeyopt","rsa_keygen_bits:2048","-out",str(private)],
                   check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    subprocess.run(["openssl","pkey","-in",str(private),"-pubout","-out",str(public)],
                   check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    signature=tmp_path/"evidence.sig"
    sign_bundle(bundle,private,signature)
    assert verify_bundle_signature(bundle,public,signature)["valid"] is True
    bundle.write_bytes(b"tampered evidence")
    assert verify_bundle_signature(bundle,public,signature)["valid"] is False

def test_missing_bundle_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Bundle does not exist"):
        sign_bundle(tmp_path/"missing.zip",tmp_path/"private.pem",tmp_path/"sig")
