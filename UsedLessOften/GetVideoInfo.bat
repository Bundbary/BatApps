@REM this file creates a json output of all of the file properties.
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

set /p "video_path=Enter the path to the video file: "
@REM set "video_path=c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\JeremyNarratedPrimary\mp4\DJI_20240724094314_0023_D.MP4"
ffprobe -v quiet -print_format json -show_format -show_streams "%video_path%" > video_info.json
pause
