#!/bin/sh
# Mac/Linux setup. MediaPipe 0.10.21 needs Python 3.10-3.12.
cd "$(dirname "$0")" || exit 1
for py in python3.12 python3.11 python3.10; do
    if command -v "$py" >/dev/null; then
        "$py" -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python -c "import cv2, mediapipe, djitellopy, pygame" && echo "READY. Now run: source .venv/bin/activate"
        exit $?
    fi
done
echo "Need Python 3.12. Install it with: brew install python@3.12"
exit 1
