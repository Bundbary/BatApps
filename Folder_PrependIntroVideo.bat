@echo off
setlocal enabledelayedexpansion
echo "this file still works if you uncomment it, by there a new one here, c:\Users\bpenn\ExpectancyLearning\BatApps\PythonBatchTools\BatchPrependIntroToPresentation\app.py"

@REM REM Get input folder path from user
@REM set /p "input_folder=Enter the path to the root folder containing videos: "

@REM REM Call the recursive function
@REM call :process_folder "%input_folder%"

@REM echo Video merging complete.
@REM pause
@REM exit /b

@REM :process_folder
@REM set "current_folder=%~1"

@REM REM Check if the current folder name contains 'backup'
@REM echo "%current_folder%" | findstr /i "backup" >nul
@REM if %errorlevel% equ 0 (
@REM     echo Skipping backup folder: %current_folder%
@REM     exit /b
@REM )

@REM REM Check for global_props.mp4 and output.mp4 in the current folder
@REM if exist "%current_folder%\global_props.mp4" (
@REM     if exist "%current_folder%\output.mp4" (
@REM         call :merge_videos "%current_folder%"
@REM     ) else (
@REM         echo Skipping folder, output.mp4 not found: %current_folder%
@REM     )
@REM ) else (
@REM     echo Skipping folder, global_props.mp4 not found: %current_folder%
@REM )

@REM REM Process subfolders
@REM for /d %%D in ("%current_folder%\*") do (
@REM     call :process_folder "%%D"
@REM )

@REM exit /b

@REM :merge_videos
@REM set "current_folder=%~1"
@REM set "intro_file=%current_folder%\global_props.mp4"
@REM set "main_file=%current_folder%\output.mp4"
@REM set "output_file=%current_folder%\presentation.mp4"

@REM REM Get duration of intro video
@REM for /f "tokens=*" %%a in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%intro_file%"') do set intro_duration=%%a
@REM set /a "fade_start=intro_duration-1"

@REM REM Get frame rate of intro video
@REM for /f "tokens=*" %%a in ('ffprobe -v error -select_streams v:0 -show_entries stream^=r_frame_rate -of default^=noprint_wrappers^=1:nokey^=1 "%intro_file%"') do set "intro_framerate=%%a"

@REM REM Prepare ffmpeg command
@REM set "filter_complex=[0:v]fps=!intro_framerate!,scale=1920:1080,fade=t=out:st=!fade_start!:d=1[v0];[1:v]fps=!intro_framerate!,fade=t=in:st=0:d=1[v1];[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[outv][outa]"

@REM REM Execute optimized ffmpeg command
@REM ffmpeg -y ^
@REM -i "%intro_file%" ^
@REM -i "%main_file%" ^
@REM -filter_complex "!filter_complex!" ^
@REM -map "[outv]" ^
@REM -map "[outa]" ^
@REM -c:v libx264 ^
@REM -preset superfast ^
@REM -crf 23 ^
@REM -c:a aac ^
@REM -b:a 192k ^
@REM -movflags +faststart ^
@REM "!output_file!"

@REM if !errorlevel! equ 0 (
@REM     echo Merged: %intro_file% and %main_file% into %output_file%
@REM ) else (
@REM     echo Error merging: %intro_file% and %main_file%
@REM     echo Please check the ffmpeg output above for details.
@REM )

@REM exit /b