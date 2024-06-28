@echo off
setlocal enabledelayedexpansion

set /p "confirm=Press Y if you want to stabilize all videos in a folder. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

set /p "input_folder=Enter the path to the folder containing the videos: "

REM Check if the folder exists
if not exist "%input_folder%" (
    echo The specified folder does not exist.
    goto :eof
)

REM Create a folder for stabilized videos
set "stabilized_folder=%input_folder%\stabilized_videos"
if not exist "%stabilized_folder%" mkdir "%stabilized_folder%"

REM Process each video file in the folder
for %%F in ("%input_folder%\*.mp4" "%input_folder%\*.avi" "%input_folder%\*.mov") do (
    set "input_file=%%F"
    set "video_name=%%~nF"
    
    echo Processing: !video_name!
    
    REM Generate transforms file
    ffmpeg -i "!input_file!" -vf vidstabdetect=shakiness=10:accuracy=15:result=transforms.trf -f null -
    
    REM Set output file path
    set "output_file=%stabilized_folder%\stabilized_!video_name!.mp4"
    
    REM Stabilize video (choose one of the following two lines)
    REM With audio:
    ffmpeg -i "!input_file!" -vf vidstabtransform=input=transforms.trf:zoom=1:smoothing=30,unsharp=5:5:0.8:3:3:0.4 -c:v libx264 -preset slow -crf 23 -acodec copy "!output_file!"
    
    REM Without audio (uncomment this line and comment the above line to remove audio):
    REM ffmpeg -i "!input_file!" -an -vf vidstabtransform=input=transforms.trf:zoom=1:smoothing=30,unsharp=5:5:0.8:3:3:0.4 -c:v libx264 -preset slow -crf 23 "!output_file!"
    
    echo Finished stabilizing !video_name!.
    echo.
    
    REM Clean up transforms file
    del transforms.trf
)

REM Output completion message
echo All videos have been stabilized. Stabilized videos are saved in: %stabilized_folder%
pause