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

REM Get root folder path from user
set /p "root_folder=Enter the root path to search for MP4 files: "

REM Check if the folder exists
if not exist "%root_folder%" (
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

echo Processing files in: %root_folder%
echo Using background music: %bg_music%

REM Process files recursively
call :ProcessFolder "%root_folder%"

echo Processing complete.
goto :end

:ProcessFolder
set "current_folder=%~1"

REM Skip folders containing "backup" in the name
echo "%current_folder%" | findstr /i "backup" >nul
if %errorlevel% equ 0 (
    echo Skipping backup folder: %current_folder%
    exit /b
)

REM Process MergedPreBGMusic.mp4 file in the current folder
if exist "%current_folder%\MergedPreBGMusic.mp4" (
    set "mp4_file=MergedPreBGMusic.mp4"
    set "output_file=MergedWithBGMusic.mp4"
    
    echo Processing: %current_folder%\!mp4_file!
    
    REM Get video duration
    for /f "delims=" %%D in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%current_folder%\!mp4_file!"') do set "video_duration=%%D"
    
    REM Calculate fade out start time
    set /a "fade_out_start=video_duration - fade_out_duration"
    
    REM Prepare background music with fade in/out
    ffmpeg -i "%bg_music%" -af "afade=t=in:st=0:d=%fade_in_duration%,afade=t=out:st=!fade_out_start!:d=%fade_out_duration%,atrim=0:!video_duration!" -acodec aac "%current_folder%\temp_bgm.m4a"
    
    REM Combine original video with new background music
    ffmpeg -i "%current_folder%\!mp4_file!" -i "%current_folder%\temp_bgm.m4a" -c:v copy -filter_complex "[0:a][1:a]amix=inputs=2:duration=longest" -c:a aac "%current_folder%\!output_file!" -y
    
    REM Remove temporary background music file
    del "%current_folder%\temp_bgm.m4a"
    
    if errorlevel 1 (
        echo Error processing !mp4_file!
    ) else (
        echo Created: !output_file!
    )
    echo.
)

REM Process subfolders
for /d %%D in ("%current_folder%\*") do (
    call :ProcessFolder "%%D"
)

exit /b

:end
echo.
echo Press any key to exit...
pause >nul

endlocal