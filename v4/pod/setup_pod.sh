#!/bin/bash
# Runs ON THE POD, once, after push_to_pod.sh has copied the files to /workspace/lg/archive.
# Recreates the Mac paths (as the multiseed pod did) by a symlink into the persistent volume,
# installs the pinned packages, and checks every input against its SHA-256.
set -euo pipefail
mkdir -p /Users/ammar
ln -sfn /workspace/lg/archive /Users/ammar/LithoGPT_archive
V4=/Users/ammar/LithoGPT_archive/LithoGPT-2/paper_atce/v4
cd "$V4"; mkdir -p logs out
# Ubuntu 24.04 images mark the system Python as externally managed (PEP 668); torch itself is
# installed there, and the container disk is thrown away on every stop, so install beside it.
PIP_BREAK_SYSTEM_PACKAGES=1 pip install --no-cache-dir -q -r pod/requirements_pod.txt
python - <<'PY'
import torch, sys
print("python", sys.version.split()[0], "torch", torch.__version__, "cuda", torch.version.cuda,
      "gpu", torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
assert torch.cuda.is_available(), "no GPU"
PY
echo "58d8da3069398641d12a3f4cca5c717198ca163ce7d5f0b0d5ce77d5932d0926  PROTOCOL.md" | sha256sum -c -
(cd cache && sha256sum -c tokenizer_v4.sha256)
echo "f72eaa9d4d30b0990b553333baaac7d129f2a2c5bce96fd580b31592658641da  /Users/ammar/LithoGPT_archive/force2020_data/train.csv" | sha256sum -c -
sha256sum -c pod/inputs.sha256
CONF=/workspace/lg/confirm/confirmatory_wells.csv
if [ -f "$CONF" ]; then sha256sum "$CONF" | tee logs/confirmatory_wells.sha256; else echo "NOTE: $CONF not present yet"; fi
nproc | sed 's/^/vCPUs /'
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo "setup OK"
