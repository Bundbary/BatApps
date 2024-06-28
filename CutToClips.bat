@echo off
setlocal enabledelayedexpansion

REM Prompt for video file path
set /p "confirm=Press Y if you want to cut a video into 10-second clips. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

set /p "input_file=Enter the path to the input video file: "

REM Get video name and folder
for %%i in ("%input_file%") do (
    set "video_name=%%~ni"
    set "video_folder=%%~dpi"
)

REM Create output folder if it doesn't exist
set "output_folder=%video_folder%%video_name%_clips"
if not exist "%output_folder%" mkdir "%output_folder%"

REM Get video duration
for /f "tokens=*" %%a in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%input_file%"') do set duration=%%a
set /a duration_int=%duration%

REM Cut video into 10-second clips
set /a clip_count=0
for /l %%i in (0,10,%duration_int%) do (
    set /a "start=%%i"
    set /a "end=%%i+10"
    if !end! gtr %duration_int% set end=%duration_int%
    set "output_file=%output_folder%\clip_!clip_count!.mp4"
    ffmpeg -i "%input_file%" -ss !start! -t 10 -c:v libx264 -preset fast -crf 22 -c:a aac -b:a 128k -avoid_negative_ts make_zero -y "!output_file!"
    set /a clip_count+=1
    if !end! geq %duration_int% goto :done
)

:done
REM Output completion message
echo Video has been cut into %clip_count% clips. Output folder: %output_folder%
pause
