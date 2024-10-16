@echo off
setlocal enabledelayedexpansion

REM Check for command line parameters
set "input_folder=%~1"
set "clip_duration=%~2"

REM If parameters are not provided, prompt for user input
if "%input_folder%"=="" (
    set /p "input_folder=Enter the path to the folder containing the videos: "
)

if "%clip_duration%"=="" (
    set /p "clip_duration=Enter the desired clip duration in seconds: "
)

REM Check if the folder exists
if not exist "%input_folder%" (
    echo The specified folder does not exist.
    goto :eof
)

REM Call the recursive function
call :ProcessFolder "%input_folder%"

REM Output completion message
echo All videos have been processed.

pause
goto :eof

:ProcessFolder
setlocal
set "folder=%~1"
for %%I in ("!folder!") do set "folder_name=%%~nxI"

REM Create a single clips folder for all videos in this directory
set "clips_folder=!folder!\!folder_name!_clips"
if not exist "!clips_folder!" mkdir "!clips_folder!"

REM Process each video file in the current folder
for %%F in ("%folder%\*.mp4" "%folder%\*.MP4") do (
    set "input_file=%%F"
    set "video_name=%%~nF"
    echo Processing: !video_name!.mp4

    REM Get video duration
    for /f "tokens=*" %%a in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "!input_file!"') do set duration=%%a
    set /a duration_int=!duration!

    REM Cut video into user-specified duration clips
    set /a clip_count=0
    for /l %%i in (0,%clip_duration%,!duration_int!) do (
        set /a "start=%%i"
        set /a "end=%%i+%clip_duration%"
        if !end! gtr !duration_int! set end=!duration_int!
        set "padded_count=00!clip_count!"
        set "output_file=!clips_folder!\!video_name!_clip_!padded_count:~-3!.mp4"
        ffmpeg -i "!input_file!" -ss !start! -t %clip_duration% -c:v libx264 -preset fast -crf 22 -c:a aac -b:a 128k -avoid_negative_ts make_zero -y "!output_file!"
        set /a clip_count+=1
    )
    echo Finished processing !video_name!.mp4. Created !clip_count! clips in !clips_folder!.
    echo.
)

REM Recursively process subfolders, excluding '_clips' folders
for /d %%D in ("%folder%\*") do (
    set "subfolder_name=%%~nxD"
    echo !subfolder_name! | findstr /i "_clips" >nul
    if errorlevel 1 (
        call :ProcessFolder "%%D"
    ) else (
        echo Skipping folder: %%D
    )
)

endlocal
goto :eof