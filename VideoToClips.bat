@echo off
setlocal enabledelayedexpansion

set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

:: Prompt for input file
set /p "input_file=Enter the path to the input video file: "

:: Prompt for output file
set /p "output_file=Enter the path for the output video file: "

:: Prompt for start time
set /p "start_time=Enter the start time (format: HH:MM:SS): "

:: Prompt for end time
set /p "end_time=Enter the end time (format: HH:MM:SS): "

:: Calculate duration
for /f "tokens=1-3 delims=:" %%a in ("%start_time%") do set /a start_seconds=%%a*3600+%%b*60+%%c
for /f "tokens=1-3 delims=:" %%a in ("%end_time%") do set /a end_seconds=%%a*3600+%%b*60+%%c
set /a duration_seconds=end_seconds-start_seconds

:: Convert duration back to HH:MM:SS format
set /a hours=duration_seconds/3600
set /a minutes=(duration_seconds%%3600)/60
set /a seconds=duration_seconds%%60
set "duration=%hours%:%minutes%:%seconds%"

:: Run FFmpeg command
ffmpeg -ss %start_time% -i "%input_file%" -t %duration% -c copy "%output_file%"

echo Clip extracted successfully!
pause