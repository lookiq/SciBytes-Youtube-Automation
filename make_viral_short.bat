@echo off
title SciBytes - Viral Video to CapCut Short Maker
cls

:: Ensure current working directory is this repository
cd /d "%~dp0"

echo ============================================================
echo      SCIBYTES VIRAL SHORT RE-ENGINEERING SYSTEM
echo ============================================================
echo.
set /p VIRAL_URL="Paste YouTube Short or Video URL: "
if "%VIRAL_URL%"=="" (
    echo.
    echo Error: No URL entered. Exiting.
    echo.
    pause
    exit /b 1
)

echo.
echo Select Action:
echo [1] Build video and PREVIEW on PC (No Upload)
echo [2] Build video and UPLOAD directly to YouTube
echo.
set /p ACTION_CHOICE="Enter 1 or 2 (Default is 1): "

if "%ACTION_CHOICE%"=="2" (
    echo.
    echo Starting Full Build and Upload to YouTube...
    python pipeline\build_from_viral.py --url "%VIRAL_URL%" --upload
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo [ERROR] Pipeline failed! Video was not uploaded.
        echo Please check the error details above.
        echo ============================================================
        pause
        exit /b 1
    )
) else (
    echo.
    echo Starting Build for PC Preview...
    python pipeline\build_from_viral.py --url "%VIRAL_URL%"
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo [ERROR] Pipeline failed! Video was not generated.
        echo Please check the error details above.
        echo ============================================================
        pause
        exit /b 1
    )
    echo.
    echo Finished! Opening video preview...
    if exist "output\scibytes_short_latest.mp4" (
        start output\scibytes_short_latest.mp4
    )
)

echo.
echo ============================================================
echo Done! Check output\scibytes_short_latest.mp4
echo ============================================================
pause
