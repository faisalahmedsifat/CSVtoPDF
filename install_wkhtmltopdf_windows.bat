@echo off
:: Download and install wkhtmltopdf on Windows
echo 🔧 Downloading wkhtmltopdf 0.12.6 for Windows...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox-0.12.6.1-2.msvc2015-win64.exe' -OutFile '%TEMP%\wkhtmltopdf_installer.exe'"
echo Installing (you may see a UAC prompt)...
"%TEMP%\wkhtmltopdf_installer.exe"
echo.
echo ✅ Installation complete!
echo    Default path: C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe
pause
