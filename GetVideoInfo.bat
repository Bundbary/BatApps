
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

set "video_path=c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\TestFootage\DJI_20240621142624_0001_D.MP4"
ffprobe -v quiet -print_format json -show_format -show_streams "%video_path%" > video_info.json
pause
