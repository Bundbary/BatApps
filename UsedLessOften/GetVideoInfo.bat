
@REM this file creates a json output of all of the file properties.
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

set /p "video_path=Enter the path to the video file: "

@REM Extract the file name without extension
for %%F in ("%video_path%") do set "file_name=%%~nF"

@REM Create the output JSON file name
set "output_file=%file_name%_video_info.json"

ffprobe -v quiet -print_format json -show_format -show_streams "%video_path%" > "%output_file%"
pause