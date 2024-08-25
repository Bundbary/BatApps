@echo off
setlocal enabledelayedexpansion

set "input_folder=%~1"
if "%input_folder%"=="" set /p "input_folder=Enter the path to the folder containing videos: "

set "log_file=%input_folder%\video_analysis.txt"
echo Video Analysis Results > "%log_file%"
echo ======================== >> "%log_file%"

for %%F in ("%input_folder%\*.mp4") do (
    echo Analyzing: %%~nxF
    echo. >> "%log_file%"
    echo File: %%~nxF >> "%log_file%"
    echo ------------------------ >> "%log_file%"
    
    ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate -of default=noprint_wrappers=1 "%%F" >> "%log_file%"
    
    ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,codec_type,sample_rate,channels -of default=noprint_wrappers=1 "%%F" >> "%log_file%"
    
    echo. >> "%log_file%"
)

echo Analysis complete. Results saved in %log_file%
pause