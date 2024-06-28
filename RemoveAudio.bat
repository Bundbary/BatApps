@echo off

set /p "confirm=Press Y if you want to remove audio from a video. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

set /p "input_file=Enter the path to the input video file: "

for %%i in ("%input_file%") do (
    set "video_name=%%~ni"
    set "video_folder=%%~dpi"
)

set "output_file=%video_folder%noaudio_%video_name%.mp4"

ffmpeg -i "%input_file%" -c:v copy -an "%output_file%"

echo Audio removed. Output file: %output_file%
pause