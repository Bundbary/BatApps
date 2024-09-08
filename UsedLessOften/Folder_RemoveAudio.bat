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

REM Create a folder for backups
set "backup_folder=%input_folder%\_backups"
if not exist "%backup_folder%" mkdir "%backup_folder%"

REM Process each video file in the folder
for %%F in ("%input_folder%\*.mp4" "%input_folder%\*.avi" "%input_folder%\*.mov") do (
    set "input_file=%%F"
    set "video_name=%%~nxF"
    
    echo Processing: !video_name!
    
    REM Move original file to backup folder
    move "!input_file!" "%backup_folder%\!video_name!"
    
    REM Create no-audio version in place of the original
    ffmpeg -i "%backup_folder%\!video_name!" -c:v copy -an "!input_file!"
    
    echo Finished processing !video_name!.
    echo.
)

REM Output completion message
echo Audio removed from all videos. Original files are backed up in: %backup_folder%
pause