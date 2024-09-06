@echo off
setlocal enabledelayedexpansion

set /p "confirm=Press Y if you want to process all videos in a folder (adjust sharpness, hue, contrast, and scale). (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

set /p "input_folder=Enter the path to the folder containing the videos: "

REM Check if the folder exists
if not exist "%input_folder%" (
    echo The specified folder does not exist.
    goto :eof
)

REM Create a folder for processed videos
set "processed_folder=%input_folder%\processed_videos"
if not exist "%processed_folder%" mkdir "%processed_folder%"

REM Process each video file in the folder
for %%F in ("%input_folder%\*.mp4" "%input_folder%\*.avi" "%input_folder%\*.mov") do (
    set "input_file=%%F"
    set "video_name=%%~nF"
    
    echo Processing: !video_name!
    
    REM Set output file path
    set "output_file=%processed_folder%\processed_!video_name!.mp4"
    
    REM Process video
    ffmpeg -i "!input_file!" -vf "unsharp=3:3:0.5:3:3:0.5,hue=h=-5:s=0.9,eq=contrast=1.1,scale=1920:1080" -c:v libx264 -preset slow -crf 23 -r 30 -c:a aac -b:a 128k -movflags +faststart "!output_file!"
    
    echo Finished processing !video_name!.
    echo.
)

REM Output completion message
echo All videos have been processed. Processed videos are saved in: %processed_folder%
pause