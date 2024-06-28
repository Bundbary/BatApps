@echo off
setlocal enabledelayedexpansion

REM Prompt for confirmation
set /p "confirm=Press Y if you want to remove audio from all videos in a folder. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

REM Prompt for folder path
set /p "input_folder=Enter the path to the folder containing the videos: "

REM Check if the folder exists
if not exist "%input_folder%" (
    echo The specified folder does not exist.
    goto :eof
)

REM Create a folder for processed videos
set "output_folder=%input_folder%\noaudio_videos"
if not exist "%output_folder%" mkdir "%output_folder%"

REM Process each video file in the folder
for %%F in ("%input_folder%\*.mp4" "%input_folder%\*.avi" "%input_folder%\*.mov") do (
    set "input_file=%%F"
    set "video_name=%%~nF"
    
    echo Processing: !video_name!
    
    set "output_file=%output_folder%\noaudio_!video_name!.mp4"
    
    ffmpeg -i "!input_file!" -c:v copy -an "!output_file!"
    
    echo Finished processing !video_name!.
    echo.
)

REM Output completion message
echo Audio removed from all videos. Processed videos are saved in: %output_folder%
pause