@echo off
setlocal enabledelayedexpansion

REM Confirmation prompt
set /p "confirm=Press Y if you want to process and optimize your videos. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

REM Get root folder path from user
set /p "root_folder=Enter the path to the root folder containing videos to process: "

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

REM Create log file
set "log_file=%root_folder%\processing_log.txt"
echo Processing started at %date% %time% > "%log_file%"

REM Initialize counters
set "total_files=0"
set "processed_count=0"

REM Count total number of video files, excluding optimized folders
for /R "%root_folder%" %%F in (*.mp4 *.avi *.mov) do (
    echo %%~dpF | findstr /i "optimized\\" >nul
    if errorlevel 1 set /a "total_files+=1"
)
echo Total video files found: %total_files%

REM Process each video file, excluding optimized folders
for /R "%root_folder%" %%F in (*.mp4 *.avi *.mov) do (
    echo %%~dpF | findstr /i "optimized\\" >nul
    if errorlevel 1 (
        set /a "processed_count+=1"
        set "input_file=%%F"
        set "input_dir=%%~dpF"
        set "file_name=%%~nxF"
        set "optimized_dir=!input_dir!optimized"
        
        echo Processing file !processed_count! of %total_files%: !file_name!
        echo Processing: !file_name! >> "%log_file%"
        
        REM Create optimized folder if it doesn't exist
        if not exist "!optimized_dir!" mkdir "!optimized_dir!"
        
        REM Process and optimize video
        ffmpeg -i "!input_file!" -c:v libx264 -preset slow -crf 23 -vf "scale=1920:1080,format=yuv420p" -r 30 -c:a aac -b:a 128k -movflags +faststart "!optimized_dir!\!file_name!" -y
        
        if !errorlevel! equ 0 (
            echo Successfully processed !file_name! >> "%log_file%"
            echo Processed: !file_name!
            
            REM Verify the processed file
            ffprobe -v error -show_entries stream=codec_name,profile,level -of default=noprint_wrappers=1 "!optimized_dir!\!file_name!" >> "%log_file%"
        ) else (
            echo Error processing !file_name! >> "%log_file%"
            echo Error: Failed to process !file_name!.
        )
        
        echo Progress: !processed_count!/%total_files% files processed.
        echo.
    )
)

echo Total videos processed: !processed_count! >> "%log_file%"
echo Processing completed at %date% %time% >> "%log_file%"
echo Video processing complete. Check %log_file% for details.
echo Total videos processed: !processed_count! out of %total_files%
pause

endlocal