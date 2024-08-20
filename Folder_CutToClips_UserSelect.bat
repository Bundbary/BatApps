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

REM Create a folder for all clips
set "all_clips_folder=%input_folder%\all_video_clips"
if not exist "%all_clips_folder%" mkdir "%all_clips_folder%"


:: Start time for time lapse
for /f "tokens=1-4 delims=:.," %%a in ("%time%") do (
    set /a "start=(((%%a*60+1%%b%%100)*60+1%%c%%100)*100+1%%d%%100)-36610100"
)

REM Process each video file in the folder
for %%F in ("%input_folder%\*.mp4" "%input_folder%\*.avi" "%input_folder%\*.mov") do (
    set "input_file=%%F"
    set "video_name=%%~nF"
    echo Processing: !video_name!

    REM Create a subfolder for this video's clips
    set "output_folder=%all_clips_folder%\!video_name!_clips"
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
        @REM set "output_file=!output_folder!\clip_!clip_count!.mp4"
        ffmpeg -i "!input_file!" -ss !start! -t %clip_duration% -c:v libx264 -preset fast -crf 22 -c:a aac -b:a 128k -avoid_negative_ts make_zero -y "!output_file!"
        set /a clip_count+=1
    )
    echo Finished processing !video_name!. Created !clip_count! clips.
    echo.
)

REM Output completion message
echo All videos have been processed. Clips are saved in: %all_clips_folder%

:: End time for time lapse
for /f "tokens=1-4 delims=:.," %%a in ("%time%") do (
    set /a "end=(((%%a*60+1%%b%%100)*60+1%%c%%100)*100+1%%d%%100)-36610100"
)

:: Calculate the duration
set /a duration=end-start
echo Duration: !duration!

pause