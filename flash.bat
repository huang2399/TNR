@echo off
setlocal
title ESP32-S3-EYE flash tool

set "HERE=%~dp0"
set "BIN=%HERE%s3eye_camera_universal_full.bin"
set "PORT=%~1"

if not exist "%BIN%" (
  echo [ERROR] firmware not found: %BIN%
  echo         put flash.bat and s3eye_camera_universal_full.bin in the same folder
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python not found. Install Python 3 and tick "Add Python to PATH".
  pause
  exit /b 1
)

python -c "import esptool" >nul 2>nul
if errorlevel 1 (
  echo [INFO] installing esptool ...
  python -m pip install -U esptool
  if errorlevel 1 (
    echo [ERROR] failed to install esptool
    pause
    exit /b 1
  )
)

if "%PORT%"=="" (
  echo [INFO] detecting serial port ...
  for /f "usebackq delims=" %%p in (`python "%HERE%detect_port.py"`) do set "PORT=%%p"
)

if "%PORT%"=="" (
  echo [ERROR] no serial port detected.
  echo         1^) plug the USB cable into the board USB port
  echo         2^) use a data-capable USB cable
  echo         3^) or specify manually:  flash.bat COM5
  pause
  exit /b 1
)

echo.
echo ==================================================
echo   firmware : s3eye_camera_universal_full.bin
echo   port     : %PORT%
echo   mode     : erase all + write (about 10 seconds)
echo ==================================================
echo.

python -m esptool --chip esp32s3 -p %PORT% -b 460800 write_flash -e --flash_mode dio --flash_size 8MB --flash_freq 80m 0x0 "%BIN%"

echo.
if errorlevel 1 (
  echo [FAILED] flashing error. Common causes:
  echo          - serial port busy ^(close the monitor / Arduino IDE^)
  echo          - wrong port, try:  flash.bat COMx
  echo          - USB cable without data lines
) else (
  echo [DONE] the board reboots automatically. The LCD should show the camera image.
  echo        For logs connect the board USB port at 115200.
)
echo.
pause