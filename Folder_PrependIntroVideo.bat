@echo off
setlocal enabledelayedexpansion

REM Get input folder path from user
set /p "input_folder=Enter the path to the root folder containing videos: "

REM Call the recursive function
call :process_folder "%input_folder%"

echo Video merging complete.
pause
exit /b

:process_folder
set "current_folder=%~1"

REM Check if the current folder name contains 'backup'
echo "%current_folder%" | findstr /i "backup" >nul
if %errorlevel% equ 0 (
    echo Skipping backup folder: %current_folder%
    exit /b
)

REM Check for global_props.mp4 and output.mp4 in the current folder
if exist "%current_folder%\global_props.mp4" (
    if exist "%current_folder%\output.mp4" (
        call :merge_videos "%current_folder%"
    ) else (
        echo Skipping folder, output.mp4 not found: %current_folder%
    )
) else (
    echo Skipping folder, global_props.mp4 not found: %current_folder%
)

REM Process subfolders
for /d %%D in ("%current_folder%\*") do (
    call :process_folder "%%D"
)

exit /b

:merge_videos
set "current_folder=%~1"
set "intro_file=%current_folder%\global_props.mp4"
set "main_file=%current_folder%\output.mp4"
set "output_file=%current_folder%\MergedPreBGMusic.mp4"

REM Get duration of intro video
for /f "tokens=*" %%a in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%intro_file%"') do set intro_duration=%%a
set /a "fade_start=intro_duration-1"

REM Get frame rate of intro video
for /f "tokens=*" %%a in ('ffprobe -v error -select_streams v:0 -show_entries stream^=r_frame_rate -of default^=noprint_wrappers^=1:nokey^=1 "%intro_file%"') do set "intro_framerate=%%a"

REM Prepare ffmpeg command
set "filter_complex=[0:v]fps=!intro_framerate!,scale=1920:1080,fade=t=out:st=!fade_start!:d=1[v0];[2:v]fps=!intro_framerate!,fade=t=in:st=0:d=1[v1];[v0][1:a][v1][2:a]concat=n=2:v=1:a=1[outv][outa]"

REM Execute optimized ffmpeg command
ffmpeg -y ^
-i "%intro_file%" ^
-f lavfi -t !intro_duration! -i anullsrc=channel_layout=stereo:sample_rate=44100 ^
-i "%main_file%" ^
-filter_complex "!filter_complex!" ^
-map "[outv]" ^
-map "[outa]" ^
-c:v libx264 ^
-preset superfast ^
-crf 23 ^
-c:a aac ^
-b:a 192k ^
-movflags +faststart ^
"!output_file!"

if !errorlevel! equ 0 (
    echo Merged: %intro_file% and %main_file% into %output_file%
) else (
    echo Error merging: %intro_file% and %main_file%
    echo Please check the ffmpeg output above for details.
)

exit /b