@echo off
setlocal enabledelayedexpansion

REM Get the input folder path
set /p "input_folder=Enter the path to the folder containing the videos: "

REM Check if the folder exists
if not exist "%input_folder%" (
    echo The specified folder does not exist.
    goto :eof
)

REM Create output folder
set "output_folder=%input_folder%\extracted_audio"
if not exist "%output_folder%" mkdir "%output_folder%"

REM Process each video file in the folder
for %%F in ("%input_folder%\*.mp4" "%input_folder%\*.avi" "%input_folder%\*.mov") do (
    set "input_file=%%F"
    set "file_name=%%~nF"
    set "output_file=%output_folder%\!file_name!.mp3"
    
    echo Processing: !file_name!
    
    ffmpeg -i "!input_file!" -vn -acodec libmp3lame -q:a 2 "!output_file!"
    
    echo Finished processing !file_name!
    echo.
)

echo All videos have been processed. Extracted audio files are saved in: %output_folder%

pause