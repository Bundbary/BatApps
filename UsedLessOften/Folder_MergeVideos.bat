@echo off
setlocal enabledelayedexpansion

REM Confirmation prompt
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

REM Get JSON file path from user
set /p "input_file=Enter the path to the JSON file: "

REM Check if ffmpeg is installed
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: ffmpeg is not installed or not in the system PATH.
    echo Please install ffmpeg and add it to your system PATH.
    pause
    exit /b 1
)


REM Check if the JSON file exists
if not exist "%input_file%" (
    echo Error: The specified JSON file does not exist.
    pause
    exit /b 1
)

REM Get the directory of the JSON file
for %%F in ("%input_file%") do set "json_dir=%%~dpF"

REM Create a temporary file to store the list of video files
set "temp_file=%temp%\video_list.txt"

REM Parse the JSON file and create the list of video files
(
    for /f "usebackq tokens=* delims=" %%a in ("%input_file%") do (
        set "line=%%a"
        set "line=!line:"=!"
        set "line=!line:,=!"
        set "line=!line: =!"
        if "!line:~0,5!"=="clip_" (
            echo file '!json_dir!!line!'
        )
    )
) > "%temp_file%"

REM Create the ffmpeg command
set "ffmpeg_cmd=ffmpeg -f concat -safe 0 -i "%temp_file%" -c copy "%json_dir%output.mp4""

REM Execute the ffmpeg command
%ffmpeg_cmd%

REM Display the content of the temp file for debugging
echo Content of %temp_file%:
type "%temp_file%"

REM Clean up the temporary file
del "%temp_file%"

echo Video merging complete. Output file: %json_dir%output.mp4
pause

endlocal