@echo off
setlocal enabledelayedexpansion

REM Confirmation prompt
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

REM Get root folder path from user
set /p "root_folder=Enter the path to the root folder containing videos to convert: "

REM Check if ffmpeg is installed
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: ffmpeg is not installed or not in the system PATH.
    echo Please install ffmpeg and add it to your system PATH.
    pause
    exit /b 1
)

REM Check if the root folder exists
if not exist "%root_folder%" (
    echo Error: The specified root folder does not exist.
    pause
    exit /b 1
)

REM Create a log file in the root folder
set "log_file=%root_folder%\conversion_log.txt"
echo Conversion started at %date% %time% > "%log_file%"
echo Root folder: %root_folder% >> "%log_file%"

REM Initialize counters
set "total_files=0"
set "processed_count=0"

REM Count total number of MP4 files in all subfolders, excluding _backup folders
for /R "%root_folder%" %%F in (*.mp4) do (
    echo %%~dpF | findstr /i "_backup\\" >nul
    if errorlevel 1 (
        set /a "total_files+=1"
    )
)
echo Total MP4 files found (excluding backup folders): %total_files%

REM Process each video file in all subfolders, excluding _backup folders
for /R "%root_folder%" %%F in (*.mp4) do (
    echo %%~dpF | findstr /i "_backup\\" >nul
    if errorlevel 1 (
        set /a "processed_count+=1"
        set "input_file=%%F"
        set "input_dir=%%~dpF"
        set "file_name=%%~nxF"
        set "backup_dir=!input_dir!_backup"
        
        echo Processing file !processed_count! of %total_files%: !file_name!
        echo Converting: !file_name! >> "%log_file%"
        
        REM Create backup folder if it doesn't exist
        if not exist "!backup_dir!" mkdir "!backup_dir!"
        
        REM Move original file to backup folder
        move "!input_file!" "!backup_dir!\!file_name!"
        
        REM Convert video
        ffmpeg -i "!backup_dir!\!file_name!" -c:v libx264 -profile:v high -preset medium -crf 23 -vf format=yuv420p -c:a aac -b:a 128k -movflags +faststart "!input_file!" -y
        
        if !errorlevel! equ 0 (
            echo Successfully converted !file_name! >> "%log_file%"
            echo Converted: !file_name!
            
            REM Verify the converted file
            ffprobe -v error -show_entries stream=codec_name,profile,level -of default=noprint_wrappers=1 "!input_file!" >> "%log_file%"
        ) else (
            echo Error converting !file_name! >> "%log_file%"
            echo Error: Failed to convert !file_name!. Restoring original file.
            move "!backup_dir!\!file_name!" "!input_file!"
        )
        
        echo Progress: !processed_count!/%total_files% files processed.
        echo.
    )
)

echo Total videos processed: !processed_count! >> "%log_file%"
echo Conversion completed at %date% %time% >> "%log_file%"
echo Video conversion complete. Check %log_file% for details.
echo Total videos processed: !processed_count! out of %total_files%
pause

endlocal