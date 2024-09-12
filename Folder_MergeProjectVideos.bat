@echo off
setlocal enabledelayedexpansion

REM Prompt for user confirmation to prevent accidental execution
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

REM Prompt the user to input the path to the folder containing global_props.json
set /p "input_folder=Enter the path to the folder containing global_props.json: "

REM Check if ffmpeg is installed and accessible in the system PATH
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: ffmpeg is not installed or not in the system PATH.
    echo Please install ffmpeg and add it to your system PATH.
    pause
    exit /b 1
)

REM Check if global_props.json exists in the specified folder
set "json_file=%input_folder%\global_props.json"
if not exist "%json_file%" (
    echo Error: global_props.json does not exist in the specified folder.
    pause
    exit /b 1
)

REM Create a temporary file to store the list of videos
set "temp_file=%TEMP%\video_list.txt"

REM Start with global_props.mp4 if it exists
if exist "%input_folder%\global_props.mp4" (
    echo file '%input_folder%\global_props.mp4' > "%temp_file%"
)

REM Read the order array from global_props.json and add to the temp file
for /f "tokens=2 delims=:," %%a in ('findstr /C:"\"order\":" "%json_file%"') do (
    set "order_line=%%~a"
    set "order_line=!order_line:[=!"
    set "order_line=!order_line:]=!"
    for %%f in (!order_line!) do (
        set "file=%%~f"
        echo file '%input_folder%\!file!' >> "%temp_file%"
    )
)

REM Extract the title from global_props.json, remove punctuation, and replace spaces with underscores
for /f "tokens=2 delims=:," %%a in ('findstr /C:"\"title\":" "%json_file%"') do (
    set "title=%%~a"
    set "title=!title:"=!"
    set "title=!title: =_!"
    for %%b in (^& ^< ^> ^^ ^| ' ^, ^. ^; ^: ^/) do set "title=!title:%%b=!"
)

if not defined title (
    echo Error: Unable to extract title from global_props.json
    pause
    exit /b 1
)

echo Extracted title: !title!

REM Construct the ffmpeg command
set "output_file=%input_folder%\!title!.mp4"
set "ffmpeg_cmd=ffmpeg -y -f concat -safe 0 -i "%temp_file%" -c copy "%output_file%""

REM Display the ffmpeg command for confirmation
echo.
echo FFmpeg command to be executed:
echo !ffmpeg_cmd!
echo.
pause
set /p "execute=Execute this command? (Y/N): "
if /i "!execute!" neq "Y" goto :eof

REM Execute the ffmpeg command to merge the videos
!ffmpeg_cmd!

REM Clean up the temporary file
del "%temp_file%"

REM Inform the user that the process is complete and show the output file location
echo.
echo Video merging complete. Output file: !output_file!
echo.
echo Press any key to close this window.
pause >nul

endlocal