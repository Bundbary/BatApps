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

:: Start time for time lapse
for /f "tokens=1-4 delims=:.," %%a in ("%time%") do (
    set /a "start=(((%%a*60+1%%b%%100)*60+1%%c%%100)*100+1%%d%%100)-36610100"
)

REM Call the recursive function
call :ProcessFolder "%input_folder%"

REM Output completion message
echo All videos have been processed. Clips are saved in [video_name]_clips folders alongside their source videos.

:: End time for time lapse
for /f "tokens=1-4 delims=:.," %%a in ("%time%") do (
    set /a "end=(((%%a*60+1%%b%%100)*60+1%%c%%100)*100+1%%d%%100)-36610100"
)

:: Calculate the duration
set /a duration=end-start
echo Duration: !duration!

pause
goto :eof

:ProcessFolder
setlocal
set "folder=%~1"

REM Process each video file in the current folder
for %%F in ("%folder%\*.mp4" "%folder%\*.avi" "%folder%\*.mov") do (
    set "input_file=%%F"
    set "video_name=%%~nF"
    echo Processing: !video_name!

    REM Create a subfolder for this video's clips, prepended with the video name
    set "output_folder=%folder%\!video_name!_clips"
    if not exist "!output_folder!" mkdir "!output_folder!"

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
        set "output_file=!output_folder!\clip_!padded_count:~-3!.mp4"
        ffmpeg -i "!input_file!" -ss !start! -t %clip_duration% -c:v libx264 -preset fast -crf 22 -c:a aac -b:a 128k -avoid_negative_ts make_zero -y "!output_file!"
        set /a clip_count+=1
    )
    echo Finished processing !video_name!. Created !clip_count! clips in !output_folder!.
    echo.
)

REM Recursively process subfolders, excluding 'backup' and '_clips' folders
for /d %%D in ("%folder%\*") do (
    set "subfolder_name=%%~nxD"
    echo !subfolder_name! | findstr /i "backup _clips" >nul
    if errorlevel 1 (
        call :ProcessFolder "%%D"
    ) else (
        echo Skipping folder: %%D
    )
)

endlocal
goto :eof