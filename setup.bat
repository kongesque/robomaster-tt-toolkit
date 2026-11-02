@echo off
rem Windows setup. Double-click this file. It installs anything missing.
cd /d "%~dp0"

call :find_python
if defined PY goto have_python
echo Installing Python 3.12...
winget install -e --id Python.Python.3.12 --architecture x64 --silent --accept-package-agreements --accept-source-agreements
call :find_python
if defined PY goto have_python
echo Could not install Python. Install Python 3.12 x64 from python.org, then run this again.
goto done

:have_python
echo Using %PY%
if exist .venv rmdir /s /q .venv
%PY% -m venv .venv
.venv\Scripts\python -m pip --version >nul 2>&1 || .venv\Scripts\python -m ensurepip --upgrade
echo Installing packages. This takes a few minutes...
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 goto failed

rem MediaPipe needs the Microsoft C++ runtime
.venv\Scripts\python -c "import cv2, mediapipe, djitellopy, pygame" >nul 2>&1
if not errorlevel 1 goto ready
echo Installing Microsoft C++ runtime...
winget install -e --id Microsoft.VCRedist.2015+.x64 --silent --accept-package-agreements --accept-source-agreements
.venv\Scripts\python -c "import cv2, mediapipe, djitellopy, pygame"
if errorlevel 1 goto failed

:ready
echo.
echo READY. Open a new terminal in this folder and run: python 0_check.py --sim
goto done

:failed
echo.
echo Setup failed. Read the error above.

:done
pause
exit /b

:find_python
rem MediaPipe has no ARM64 build, so skip ARM64 Python.
set "PY="
py -3.12 -c "import platform, sys; sys.exit(platform.machine() == 'ARM64')" >nul 2>&1 && set "PY=py -3.12" && exit /b
for %%p in ("%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%ProgramFiles%\Python312\python.exe") do if exist %%p set PY=%%p
exit /b
