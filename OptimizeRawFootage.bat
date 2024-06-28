
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

set "input_file=c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\TestFootage\DJI_20240621144202_0007_D\DJI_20240621144202_0007_D.MP4"
ffmpeg -i "%input_file%" -c:v libx264 -preset slow -crf 23 -vf scale=1920:1080 -r 30 -c:a aac -b:a 128k -movflags +faststart output.mp4
pause
