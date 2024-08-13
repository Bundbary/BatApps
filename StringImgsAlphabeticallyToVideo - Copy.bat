@echo off

setlocal enabledelayedexpansion

set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "

if /i "%confirm%" neq "Y" goto :eof

rem Set the input folder, output file, and desired height
set "input_folder=temp"
set "output_file=output.mp4"
set "height=720"

rem Create a temporary file list
if exist temp_file_list.txt del temp_file_list.txt

rem Generate the file list and resize images
set "n=0"

for %%f in ("%input_folder%\*.jpg" "%input_folder%\*.png") do (
    set "infile=%%f"
    set "outfile=temp_%%~nf.png"
    set "outfile=!outfile:"=!"
    echo Processing: !infile!
    ffmpeg -i "!infile!" -vf "scale=-2:%height%" "!outfile!" -v error
    if !errorlevel! neq 0 (
        echo Error processing file: !infile!
        goto :error
    )
    echo file '!outfile!' >> temp_file_list.txt
    echo duration 2 >> temp_file_list.txt
    set /a n+=1
)

rem Create the video
echo Creating video...
ffmpeg -f concat -safe 0 -i temp_file_list.txt -vsync vfr -pix_fmt yuv420p -c:v libx264 -preset medium -crf 23 "%output_file%" -v verbose

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