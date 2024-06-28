
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

ffmpeg -i "c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\TestFootage\DJI_20240621144202_0007_D\DJI_20240621144202_0007_D_Optimized.MP4" -vf "unsharp=3:3:0.5:3:3:0.5,hue=h=-5:s=0.9,eq=contrast=1.1,scale=1920:1080" -c:v libx264 -preset slow -crf 23 -r 30 -c:a aac -b:a 128k -movflags +faststart output.mp4
pause
