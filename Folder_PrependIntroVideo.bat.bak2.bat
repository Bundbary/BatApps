@echo off
setlocal enabledelayedexpansion

REM Get input and output folder paths from user
set /p "input_folder=Enter the path to the folder containing processed intro and main videos: "
set /p "output_folder=Enter the path to the output folder: "

REM Create output folder if it doesn't exist
if not exist "%output_folder%" mkdir "%output_folder%"

REM Process each intro and main video pair
for %%I in ("%input_folder%\*_intro_.mp4") do (
    set "intro_file=%%~nxI"
    set "main_file=!intro_file:_intro_=_main_!"
    
    if exist "%input_folder%\!main_file!" (
        set "output_file=%output_folder%\merged_!main_file:_main_=!"
        
        REM Get duration of intro video
        for /f "tokens=*" %%a in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%input_folder%\!intro_file!"') do set intro_duration=%%a
        set /a "fade_start=intro_duration-1"
        
        REM Prepare ffmpeg command
        set "filter_complex=[0:v]scale=1920:1080,fade=t=out:st=!fade_start!:d=1[v0];[2:v]fade=t=in:st=0:d=1[v1];[v0][1:a][v1][2:a]concat=n=2:v=1:a=1[outv][outa]"
        
        REM Execute ffmpeg command
        ffmpeg -y -i "%input_folder%\!intro_file!" -f lavfi -t !intro_duration! -i anullsrc=channel_layout=stereo:sample_rate=44100 -i "%input_folder%\!main_file!" ^
        -filter_complex "!filter_complex!" ^
        -map "[outv]" -map "[outa]" ^
        -c:v libx264 -crf 18 -preset medium -c:a aac -b:a 192k ^
        "!output_file!"
        
        if !errorlevel! equ 0 (
            echo Merged: !intro_file! and !main_file!
        ) else (
            echo Error merging: !intro_file! and !main_file!
            echo Please check the ffmpeg output above for details.
        )
    ) else (
        echo Error: Main video for !intro_file! not found
    )
)

echo Video merging complete.
pause