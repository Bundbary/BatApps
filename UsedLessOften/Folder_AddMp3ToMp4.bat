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
set /p "confirm=NOTE: The python app, Batch_transcript_to_voice currently does this in our video process, but this file does still work.       Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :end

REM Get folder path from user
set /p "input_folder=Enter the path to the folder containing MP3 and MP4 files: "

REM Check if the folder exists
if not exist "%input_folder%" (
    echo Error: The specified folder does not exist.
    goto :end
)

echo Processing files in: %input_folder%

REM Call the recursive function
call :ProcessFolder "%input_folder%"

echo Processing complete.
echo New video files with added audio have been saved in their respective folders.

goto :end

:ProcessFolder
REM Check if the current folder name contains 'backup'
echo %~1 | findstr /i "backup" >nul
if %errorlevel% equ 0 (
    echo Skipping backup folder: %~1
    exit /b
)

REM Process each MP3 file ending with "_transcript.mp3" in the current folder
for %%F in ("%~1\*_transcript.mp3") do (
    set "mp3_file=%%~nxF"
    set "mp4_file=%%~nF"
    set "mp4_file=!mp4_file:_transcript=!"
    set "output_file=!mp4_file!_audio.mp4"
    
    if exist "%~1\!mp4_file!.mp4" (
        echo Processing: !mp3_file! and !mp4_file!.mp4
        ffmpeg -i "%~1\!mp4_file!.mp4" -i "%~1\!mp3_file!" -c:v copy -c:a aac -strict experimental "%~1\!output_file!" -y
        if errorlevel 1 (
            echo Error processing !mp4_file!.mp4 with !mp3_file!
        ) else (
            echo Created: !output_file!
        )
    ) else (
        echo No matching MP4 file found for !mp3_file!
    )
    echo.
)

REM Recursively process subfolders
for /d %%D in ("%~1\*") do (
    call :ProcessFolder "%%~fD"
)

exit /b

:end
echo.
echo Press any key to exit...
pause >nul

endlocal