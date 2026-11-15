@echo off
title YouTube Raw Video Editing Watcher
cd /d "%~dp0"
echo =====================================================================
echo  Starting YouTube Raw Video Watcher...
echo  Drop your recorded videos into the "raw" folder.
echo  The pipeline will automatically edit them and output to "out".
echo =====================================================================
python scripts\process.py --watch
pause

