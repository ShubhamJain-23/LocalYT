@echo off
echo =========================================
echo       LocalYT Folder Manager
echo =========================================
echo.
echo Current folders:
type folders.txt
echo.
echo =========================================
set /p folderPath="Paste the full path to your new video folder (or press Enter to exit): "
if "%folderPath%"=="" goto end

echo %folderPath%>> folders.txt
echo.
echo Reconfiguring Docker and restarting...
powershell.exe -ExecutionPolicy Bypass -File generate_override.ps1
docker-compose up -d
echo.
echo Done! Your new folder has been added.
:end
pause
