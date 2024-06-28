
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

set /p "input_file=Enter the path to the input video file: "

ffmpeg -i "%input_file%" -vf vidstabdetect=shakiness=10:accuracy=15:result=transforms.trf -f null -

for %%i in ("%input_file%") do (
    set "video_name=%%~ni"
    set "video_folder=%%~dpi"
)

set "output_file=%video_folder%stabilized_%video_name%.mp4"

@REM this line stabilizes without removing audio. COMMENT ONE OF THESE LINES OUT!!
@REM ffmpeg -i "%input_file%" -vf vidstabtransform=input=transforms.trf:zoom=1:smoothing=30,unsharp=5:5:0.8:3:3:0.4 -c:v libx264 -preset slow -crf 23 -acodec copy "%output_file%"

@REM this line removes audio, too.
ffmpeg -i "%input_file%" -an -vf vidstabtransform=input=transforms.trf:zoom=1:smoothing=30,unsharp=5:5:0.8:3:3:0.4 -c:v libx264 -preset slow -crf 23 -acodec copy "%output_file%"







echo Video stabilization completed. Output file: %output_file%
pause