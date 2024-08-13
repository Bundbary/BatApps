@echo off
setlocal enabledelayedexpansion



set /p "confirm=Press Y if you want to continue. (Y/N): "
if /i "%confirm%" neq "Y" goto :eof



rem Set the input video file name
set "input_file=c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\JeremyNarratedPrimary\mp4\DJI_20240724094314_0023_D.MP4"
@echo off
setlocal enabledelayedexpansion

rem Set the output audio file names
set "output_mp3=%input_file:.MP4=.mp3%"
set "output_wav=%input_file:.MP4=.wav%"

rem Extract audio as MP3
echo Extracting MP3...
ffmpeg -i "%input_file%" -vn -acodec libmp3lame -q:a 2 "%output_mp3%"

rem Extract audio as WAV
echo Extracting WAV...
ffmpeg -i "%input_file%" -vn -acodec pcm_s16le "%output_wav%"

rem Check if the output files were created successfully
if exist "%output_mp3%" (
    echo MP3 extraction complete. Output file: %output_mp3%
) else (
    echo Error: MP3 extraction failed.
)

if exist "%output_wav%" (
    echo WAV extraction complete. Output file: %output_wav%
) else (
    echo Error: WAV extraction failed.
)

pause