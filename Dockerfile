FROM ubuntu:24.04

# Avoid interactive prompts during package install
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System dependencies:
# - python3.12 + pip for the app
# - python3-tk for Tkinter GUI
# - stockfish engine
# - PortAudio/ALSA for sounddevice
# - libgl/libglib for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv python3-tk \
    stockfish \
    portaudio19-dev libasound2-dev libjack-jackd2-0 \
    libcairo2 libcairo2-dev libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 fonts-dejavu-core \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python virtualenv to avoid PEP 668 constraints
RUN python3 -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# App sources (includes Vosk model under chess_system/)
COPY chess_system ./chess_system
COPY samples ./samples
COPY README.md ./README.md

# Run from chess_system so relative model path resolves
WORKDIR /app/chess_system
CMD ["python3", "main.py"]
