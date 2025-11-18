#!/usr/bin/env bash
set -euo pipefail

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer targets Ubuntu/Debian (needs apt-get)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/3] Installing system packages (sudo required)…"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  python3 python3-venv python3-pip python3-tk \
  portaudio19-dev libasound2-dev libjack-jackd2-0 \
  libcairo2 libcairo2-dev libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 \
  libgdk-pixbuf-2.0-0 fonts-dejavu-core \
  libgl1 libglib2.0-0 \
  stockfish \
  alsa-utils

echo "[2/3] Creating virtual environment at .speech…"
python3 -m venv .speech
source .speech/bin/activate

echo "[3/3] Installing Python dependencies…"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Done. To run:"

