@echo off

setlocal enabledelayedexpansion

set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "

if /i "%confirm%" neq "Y" goto :eof

rem Set the input folder, output file, and desired height
set "input_folder=temp"
set "output_file=output.mp4"
set "height=720"
set "framerate=25"
set "transition_duration=0.5"
set "image_duration=1.5"

rem Create a temporary file list
if exist temp_file_list.txt del temp_file_list.txt

rem Generate the file list and resize images
set "n=0"
for %%f in ("%input_folder%\*.jpg" "%input_folder%\*.png") do (
    set /a n+=1
    echo file 'temp_!n!.png' >> temp_file_list.txt
    ffmpeg -i "%%f" -vf "scale=-2:%height%" "temp_!n!.png" -y
)

rem Create the video with transitions
echo Creating video with transitions...
ffmpeg -f concat -safe 0 -i temp_file_list.txt ^
       -filter_complex "zoompan=d=%image_duration%:s=788x720:fps=%framerate%,framerate=fps=%framerate%" ^
       -c:v libx264 -pix_fmt yuv420p "%output_file%"

if !errorlevel! neq 0 goto :error

echo Video creation complete: %output_file%

rem Clean up temporary files
del temp_*.png
del temp_file_list.txt

goto :eof

:error
echo Error: Video creation failed.
echo Temporary files have not been deleted for debugging purposes.
exit /b 1