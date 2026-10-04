"""Install a pinned official Mihomo release, verified against release SHA-256."""
import gzip
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

VERSION = 'v1.19.32'
EXPECTED = 'ba3ce607747a07f948fc35780e108a4a7c7f552a38b9bd4d115f313ebcb89c20'
URL = f'https://github.com/MetaCubeX/mihomo/releases/download/{VERSION}/mihomo-linux-amd64-compatible-{VERSION}.gz'


def main():
    target = Path(os.environ.get('MIHOMO_BIN', '/tmp/free-node-mihomo'))
    with tempfile.TemporaryDirectory() as folder:
        archive = Path(folder) / 'mihomo.gz'
        subprocess.run(['curl', '-fsSL', '--retry', '2', '--max-time', '120', URL, '-o', str(archive)], check=True)
        data = archive.read_bytes()
        if hashlib.sha256(data).hexdigest() != EXPECTED:
            raise RuntimeError('Mihomo checksum mismatch')
        target.write_bytes(gzip.decompress(data))
        target.chmod(0o700)
    subprocess.run([str(target), '-v'], check=True)


if __name__ == '__main__':
    main()
