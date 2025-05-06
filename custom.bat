@echo off
cd /d %~dp0

REM switch console to UTF‑8 codepage
chcp 65001 >nul

REM ensure Python uses UTF‑8 for stdout/stderr
set PYTHONIOENCODING=utf-8

REM Activate the virtual environment
call .venv\Scripts\activate.bat

REM Run the Python script
python custom.py

REM if python failed, show error code
if %ERRORLEVEL% neq 0 echo Python exited with code %ERRORLEVEL%

pause