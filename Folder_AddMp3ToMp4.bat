@echo off
setlocal enabledelayedexpansion

REM Check if ffmpeg is installed
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: ffmpeg is not installed or not in the system PATH.
    echo Please install ffmpeg and add it to your system PATH.
    goto :end
)


REM Confirmation prompt
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :end

REM Get folder path from user
set /p "input_folder=Enter the path to the folder containing MP3 and MP4 files: "

REM Check if the folder exists
if not exist "%input_folder%" (
    echo Error: The specified folder does not exist.
    goto :end
)

echo Processing files in: %input_folder%

REM Process each MP3 file in the folder
for %%F in ("%input_folder%\*.mp3") do (
    set "mp3_file=%%~nxF"
    set "mp4_file=%%~nF.mp4"
    set "output_file=%%~nF_audio.mp4"
    
    if exist "%input_folder%\!mp4_file!" (
        echo Processing: !mp3_file! and !mp4_file!
        ffmpeg -i "%input_folder%\!mp4_file!" -i "%input_folder%\!mp3_file!" -c:v copy -c:a aac -strict experimental "%input_folder%\!output_file!" -y
        if errorlevel 1 (
            echo Error processing !mp4_file! with !mp3_file!
        ) else (
            echo Created: !output_file!
        )
    ) else (
        echo No matching MP4 file found for !mp3_file!
    )
    echo.
)

echo Processing complete.
echo New video files with added audio have been saved in: %input_folder%

:end
echo.
echo Press any key to exit...
pause >nul

endlocal