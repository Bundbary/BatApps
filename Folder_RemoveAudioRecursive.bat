@echo off
setlocal enabledelayedexpansion

REM Prompt for confirmation
set /p "confirm=Press Y if you want to remove audio from all videos recursively in a folder. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

REM Prompt for folder path
set /p "root_folder=Enter the path to the root folder containing the videos: "

REM Check if the folder exists
if not exist "%root_folder%" (
    echo The specified folder does not exist.
    goto :eof
)

REM Call the recursive function
call :ProcessFolder "%root_folder%"

echo All videos have been processed.
pause
goto :eof

:ProcessFolder
setlocal
set "current_folder=%~1"

REM Create a _backups folder in the current folder
set "backup_folder=%current_folder%\_backups"
if not exist "%backup_folder%" mkdir "%backup_folder%"

REM Process mp4 files in the current folder
for %%F in ("%current_folder%\*.mp4") do (
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

REM Recursively process subfolders, skipping those with 'backup' in the name
for /d %%D in ("%current_folder%\*") do (
    set "folder_name=%%~nxD"
    echo !folder_name! | findstr /i "backup" >nul
    if errorlevel 1 (
        call :ProcessFolder "%%D"
    ) else (
        echo Skipping backup folder: %%D
    )
)

pause
endlocal
exit /b