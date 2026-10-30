@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -r requirements-build.txt || (pause & exit /b 1)
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name CSVDataQualityLab --add-data "assets\complete.wav;assets" main.py
if errorlevel 1 (echo Build failed & pause & exit /b 1)
echo Build complete. Test dist\CSVDataQualityLab.exe on Windows.
pause
endlocal
