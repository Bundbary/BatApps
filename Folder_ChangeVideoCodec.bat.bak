@echo off
setlocal enabledelayedexpansion

REM Confirmation prompt
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

REM Get input and output folder paths from user
set /p "input_folder=Enter the path to the folder containing videos to convert: "
set /p "output_folder=Enter the path to the output folder for converted videos: "

REM Check if ffmpeg is installed
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: ffmpeg is not installed or not in the system PATH.
    echo Please install ffmpeg and add it to your system PATH.
    pause
    exit /b 1
)

REM Check if the input folder exists
if not exist "%input_folder%" (
    echo Error: The specified input folder does not exist.
    pause
    exit /b 1
)

REM Create output folder if it doesn't exist
if not exist "%output_folder%" mkdir "%output_folder%"

REM Create a log file
set "log_file=%output_folder%\conversion_log.txt"
echo Conversion started at %date% %time% > "%log_file%"

REM Log input and output folder paths
echo Input folder: %input_folder% >> "%log_file%"
echo Output folder: %output_folder% >> "%log_file%"

REM Count total number of MP4 files
set "total_files=0"
for %%F in ("%input_folder%\*.mp4") do set /a "total_files+=1"
echo Total MP4 files found: %total_files%

REM Initialize a counter for processed videos
set "processed_count=0"

REM Process each video file
for %%F in ("%input_folder%\*.mp4") do (
    set /a "processed_count+=1"
    set "input_file=%%~nxF"
    set "output_file=%output_folder%\converted_%%~nxF"
    
    echo Processing file !processed_count! of %total_files%: !input_file!
    echo Converting: !input_file! >> "%log_file%"
    
    REM Convert video to H.264 codec with AAC audio (WMP compatible)
    ffmpeg -i "%input_folder%\!input_file!" -c:v libx264 -profile:v high -preset medium -crf 23 -vf format=yuv420p -c:a aac -b:a 128k -movflags +faststart "!output_file!" -y
    
    if !errorlevel! equ 0 (
        echo Successfully converted !input_file! >> "%log_file%"
        echo Converted: !input_file!
        
        REM Verify the converted file
        ffprobe -v error -show_entries stream=codec_name,profile,level -of default=noprint_wrappers=1 "!output_file!" >> "%log_file%"
    ) else (
        echo Error converting !input_file! >> "%log_file%"
        echo Error: Failed to convert !input_file!. Check the log for details.
    )
    
    echo Progress: !processed_count!/%total_files% files processed.
    echo.
)

echo Total videos converted: !processed_count! >> "%log_file%"
echo Conversion completed at %date% %time% >> "%log_file%"
echo Video conversion complete. Check %log_file% for details.
echo Total videos converted: !processed_count! out of %total_files%
pause

endlocal