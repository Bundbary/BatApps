@echo off
setlocal enabledelayedexpansion

REM Get the input folder path
set /p "input_folder=Enter the path to the folder containing the videos: "

REM Check if the folder exists
if not exist "%input_folder%" (
    echo The specified folder does not exist.
    goto :eof
)

echo Starting to process videos in %input_folder% and its subfolders...
echo.

REM Process videos recursively
call :ProcessFolder "%input_folder%"

echo.
echo All videos have been processed.

pause
goto :eof

:ProcessFolder
echo Entering folder: %~1
REM Process each video file in the current folder
for %%F in ("%~1\*.mp4" "%~1\*.avi" "%~1\*.mov") do (
    set "input_file=%%F"
    set "file_name=%%~nF"
    set "output_file=%%~dpnF.mp3"
    
    REM Check if the output file already exists
    if exist "!output_file!" (
        echo Skipping !file_name! (output already exists^)
    ) else (
        echo Processing: !file_name!
        ffmpeg -i "!input_file!" -vn -acodec libmp3lame -q:a 2 "!output_file!"
        if !errorlevel! equ 0 (
            echo Finished processing !file_name!
        ) else (
            echo Error processing !file_name!
        )
    )
    echo.
)

REM Process subfolders (excluding _backup)
for /d %%D in ("%~1\*") do (
    if /i not "%%~nxD"=="_backup" (
        call :ProcessFolder "%%D"
    )
)

goto :eof