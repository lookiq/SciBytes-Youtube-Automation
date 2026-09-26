@echo off
title SciBytes - Viral Trend Hunter & Short Generator
cls

:: Ensure current working directory is this repository
cd /d "%~dp0"

echo ============================================================
echo      SCIBYTES VIRAL SHORT RE-ENGINEERING SYSTEM
echo ============================================================
echo.
echo Select Mode:
echo [1] AUTONOMOUS VIRAL HUNTER: Auto-find #1 Trending Video & Preview (No link needed!)
echo [2] AUTONOMOUS VIRAL HUNTER: Auto-find #1 Trending Video & Upload to YouTube
echo [3] VIEW TRENDING RANKINGS: Discover Top 5 Space Shorts by VPH
echo [4] MANUAL LINK: Paste a specific YouTube Short link to Re-engineer
echo.
set /p MODE="Enter 1, 2, 3, or 4 (Default is 1): "
if "%MODE%"=="" set MODE=1

if "%MODE%"=="3" (
    echo.
    echo Scanning YouTube for highest VPH space shorts...
    python pipeline\viral_trend_hunter.py --hunt
    echo.
    pause
    exit /b 0
)

if "%MODE%"=="1" (
    echo.
    echo Running Autonomous Viral Hunter for PC Preview...
    python pipeline\viral_trend_hunter.py --auto
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo [ERROR] Pipeline failed! Please check details above.
        echo ============================================================
        pause
        exit /b 1
    )
    echo.
    echo Finished! Opening video preview...
    if exist "output\scibytes_short_latest.mp4" (
        start output\scibytes_short_latest.mp4
    )
    echo.
    echo ============================================================
    echo Done! Check output\scibytes_short_latest.mp4
    echo ============================================================
    pause
    exit /b 0
)

if "%MODE%"=="2" (
    echo.
    echo Running Autonomous Viral Hunter and Direct YouTube Upload...
    python pipeline\viral_trend_hunter.py --auto-upload
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo [ERROR] Pipeline failed! Please check details above.
        echo ============================================================
        pause
        exit /b 1
    )
    echo.
    echo ============================================================
    echo Done! Video generated and uploaded to YouTube!
    echo ============================================================
    pause
    exit /b 0
)

if "%MODE%"=="4" (
    echo.
    set /p VIRAL_URL="Paste YouTube Short or Video URL: "
    if "%VIRAL_URL%"=="" (
        echo Error: No URL entered. Exiting.
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
            echo [ERROR] Pipeline failed! Video was not uploaded.
            pause
            exit /b 1
        )
    ) else (
        echo.
        echo Starting Build for PC Preview...
        python pipeline\build_from_viral.py --url "%VIRAL_URL%"
        if errorlevel 1 (
            echo.
            echo [ERROR] Pipeline failed! Video was not generated.
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
    exit /b 0
)
