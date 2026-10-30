@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)
%PY% -c "import PyQt6" >nul 2>nul
if errorlevel 1 (
  echo Installing PyQt6 - an internet connection may be required.
  %PY% -m pip install -r requirements.txt || (pause & exit /b 1)
)
%PY% main.py
if errorlevel 1 pause
endlocal
