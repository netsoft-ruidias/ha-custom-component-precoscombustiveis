# Minimal Home Assistant dev image for testing this custom component
ARG HA_VERSION=stable
FROM ghcr.io/home-assistant/home-assistant:${HA_VERSION}

# Work inside the HA config directory
WORKDIR /config

# Install only the custom component's extra Python deps (skip the bundled homeassistant)
COPY requirements.txt /tmp/requirements.txt
RUN python - <<'PY'
from pathlib import Path
import subprocess
import sys

req_path = Path('/tmp/requirements.txt')
lines = [line.strip() for line in req_path.read_text().splitlines() if line.strip() and not line.startswith('#')]
filtered = [line for line in lines if not line.startswith('homeassistant')]
if filtered:
    tmp = Path('/tmp/filtered_requirements.txt')
    tmp.write_text('\n'.join(filtered) + '\n')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', '-r', str(tmp)])
PY
