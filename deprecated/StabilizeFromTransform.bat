
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof


ffmpeg -i "c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\TestFootage\DJI_20240621143348_0003_D\DJI_20240621143348_0003_D_SharpenHueContrast.MP4" -vf vidstabtransform=input=transforms.trf:zoom=1:smoothing=30,unsharp=5:5:0.8:3:3:0.4 -c:v libx264 -preset slow -crf 23 -acodec copy output_stabilized.mp4
pause