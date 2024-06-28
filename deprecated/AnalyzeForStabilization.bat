
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

ffmpeg -i "c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\TestFootage\DJI_20240621143348_0003_D\DJI_20240621143348_0003_D_SharpenHueContrast.MP4" -vf vidstabdetect=shakiness=10:accuracy=15:result=transforms.trf -f null -
pause
