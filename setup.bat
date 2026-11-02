@echo off
rem Windows setup. MediaPipe 0.10.21 needs Python 3.10-3.12.
cd /d "%~dp0"
py -3.12 -m venv .venv || py -3.11 -m venv .venv || py -3.10 -m venv .venv || (echo Install Python 3.12 from python.org & exit /b 1)
.venv\Scripts\pip install -r requirements.txt && .venv\Scripts\python -c "import cv2, mediapipe, djitellopy, pygame" && echo READY. Now run: python 0_check.py --sim
