@echo off
setlocal enabledelayedexpansion

REM Confirmation prompt
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

REM Get input and output folder paths from user
set /p "input_folder=Enter the path to the folder containing converted videos: "
set /p "output_folder=Enter the path to the output folder for merged videos: "

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
set "log_file=%output_folder%\merge_log.txt"
echo Merging started at %date% %time% > "%log_file%"

REM Log input and output folder paths
echo Input folder: %input_folder% >> "%log_file%"
echo Output folder: %output_folder% >> "%log_file%"

REM Initialize a counter for processed videos
set "processed_count=0"

REM Process each intro and main video pair
for %%I in ("%input_folder%\converted_*_intro_.mp4") do (
    set "intro_file=%%~nxI"
    set "main_file=!intro_file:_intro_=_main_!"
    
    echo Checking for intro file: !intro_file! >> "%log_file%"
    echo Checking for main file: !main_file! >> "%log_file%"
    
    if exist "%input_folder%\!main_file!" (
        echo Found matching pair: !intro_file! and !main_file! >> "%log_file%"
        echo Merging: !intro_file! and !main_file!
        
        REM Create a temporary file to store the list of video files
        set "temp_file=%temp%\video_list.txt"
        
        REM Create the list of video files
        (
            echo file '%input_folder%\!intro_file!'
            echo file '%input_folder%\!main_file!'
        ) > "!temp_file!"
        
        REM Create the ffmpeg command
        set "output_file=%output_folder%\merged_!main_file:converted_=!"
        set "ffmpeg_cmd=ffmpeg -f concat -safe 0 -i "!temp_file!" -c copy "!output_file!""
        
        echo Executing command: !ffmpeg_cmd! >> "%log_file%"
        
        REM Execute the ffmpeg command
        !ffmpeg_cmd!
        
        if !errorlevel! equ 0 (
            echo Successfully merged !intro_file! and !main_file! >> "%log_file%"
            set /a "processed_count+=1"
        ) else (
            echo Error merging !intro_file! and !main_file! >> "%log_file%"
        )
        
        REM Clean up the temporary file
        del "!temp_file!"
    ) else (
        echo Error: Main video for !intro_file! not found >> "%log_file%"
    )
)

echo Total videos merged: !processed_count! >> "%log_file%"
echo Merging completed at %date% %time% >> "%log_file%"
echo Video merging complete. Check %log_file% for details.
echo Total videos merged: !processed_count!
pause

endlocal