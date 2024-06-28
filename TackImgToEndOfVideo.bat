@echo off
setlocal enabledelayedexpansion

set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof

rem Set the folder paths
set "video_folder=c:\Users\bpenn\ExpectancyLearning\flask_apps\BatchImgs\app\images\MonkeyPaw\img_to_vid\"
set "image_folder=c:\Users\bpenn\ExpectancyLearning\flask_apps\BatchImgs\app\images\MonkeyPaw\"
set "output_folder=c:\Users\bpenn\ExpectancyLearning\flask_apps\BatchImgs\app\images\MonkeyPaw\img_to_vid\VidWithImg\"

rem Loop through video files
for %%V in ("%video_folder%*.mp4") do (
    set "video_name=%%~nV"
    set "video_file=!video_folder!%%~nV.mp4"

    rem Get video dimensions
    for /f "tokens=1,2" %%a in ('ffprobe -v error -select_streams v:0 -show_entries stream^=width^,height -of csv^=s^=x:p^=0 "!video_file!"') do (
        set "video_width=%%a"
        set "video_height=%%b"
    )

    echo Video dimensions: !video_width!x!video_height!

    rem Find corresponding image file
    set "image_file=!image_folder!!video_name!.png"
    set "output_file=!output_folder!!video_name!.mp4"

    if exist "!image_file!" (
        rem Scale image to match video resolution
        ffmpeg -i "!image_file!" -vf scale=!video_width!:!video_height! "!image_folder!scaled_!video_name!.png"
        set "scaled_image_file=!image_folder!scaled_!video_name!.png"

        rem Check if the scaled image file was created
        if exist "!scaled_image_file!" (
            rem Create a video from the scaled image
            ffmpeg -loop 1 -t 10 -i "!scaled_image_file!" -vf format=yuv420p -c:v libx264 -pix_fmt yuv420p "!image_folder!video_!video_name!.mp4"
            set "image_video_file=!image_folder!video_!video_name!.mp4"

            rem Normalize the frame rate of both video streams
            ffmpeg -i "!video_file!" -r 25 "!video_folder!normalized_!video_name!.mp4"
            set "normalized_video_file=!video_folder!normalized_!video_name!.mp4"
            set "output_file=!output_file: =_!.mp4"

            ffmpeg -i "!normalized_video_file!" -i "!image_video_file!" -filter_complex "[0:v][1:v]xfade=transition=fade:duration=1:offset=3[v]" -map "[v]" -c:v libx264 -c:a aac -strict experimental "!output_file!"

            rem Delete the temporary files after use
            del "!scaled_image_file!"
            del "!image_video_file!"
            del "!normalized_video_file!"
        ) else (
            echo Failed to create scaled image file: !scaled_image_file!
        )
    ) else (
        echo Image file not found: !image_file!
    )
)

endlocal
pause