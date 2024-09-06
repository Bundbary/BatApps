@echo off
setlocal enabledelayedexpansion

REM User-configurable fade durations (in seconds)
set "fade_in_duration=3"
set "fade_out_duration=3"

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
set /p "input_folder=Enter the path to the folder containing MP4 files: "

REM Check if the folder exists
if not exist "%input_folder%" (
    echo Error: The specified folder does not exist.
    goto :end
)

REM Get background music MP3 file path from user
set /p "bg_music=Enter the full path to the background music MP3 file: "

REM Check if the MP3 file exists
if not exist "%bg_music%" (
    echo Error: The specified MP3 file does not exist.
    goto :end
)

echo Processing files in: %input_folder%
echo Using background music: %bg_music%

REM Process each MP4 file in the folder
for %%F in ("%input_folder%\*.mp4") do (
    set "mp4_file=%%~nxF"
    set "output_file=%%~nF_bgmusic.mp4"
    
    echo Processing: !mp4_file!
    
    REM Get video duration
    for /f "delims=" %%D in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%%F"') do set "video_duration=%%D"
    
    REM Calculate fade out start time
    set /a "fade_out_start=video_duration - fade_out_duration"
    
    ffmpeg -i "%%F" -i "%bg_music%" -filter_complex "[1:a]afade=t=in:st=0:d=%fade_in_duration%,apad,atrim=0:!video_duration!,afade=t=out:st=!fade_out_start!:d=%fade_out_duration%[audio]" -map 0:v -map "[audio]" -c:v copy -c:a aac -strict experimental "%input_folder%\!output_file!" -y
    
    if errorlevel 1 (
        echo Error processing !mp4_file!
    ) else (
        echo Created: !output_file!
    )
    echo.
)

echo Processing complete.
echo New video files with added background music have been saved in: %input_folder%

:end
echo.
echo Press any key to exit...
pause >nul

endlocal