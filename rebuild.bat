@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Steam Analysis - Rebuild ===
echo.

echo [1/3] analysis_v2.py ...
python scripts\analysis_v2.py
if errorlevel 1 (
    echo ERROR: analysis_v2.py failed
    pause
    exit /b 1
)

echo.
echo [2/3] build_game_names_final.py ...
python scripts\build_game_names_final.py
if errorlevel 1 (
    echo ERROR: build_game_names_final.py failed
    pause
    exit /b 1
)

echo.
echo [3/3] embed_v2.py ...
python scripts\embed_v2.py
if errorlevel 1 (
    echo ERROR: embed_v2.py failed
    pause
    exit /b 1
)

echo.
echo === Done ===
start "" index_standalone.html
