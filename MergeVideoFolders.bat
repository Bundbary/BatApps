@echo off
setlocal enabledelayedexpansion



@REM set "folder1=c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\080924_Narrated_Raw\optimized_videos\all_video_clips\ Start-Up_Prep_Best_Practices_-_Run_Rate___Audio_Good_Video_Not_clips"

@REM set "folder2=c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\080924_Narrated_Raw\optimized_videos\all_video_clips\Start-Up_Prep_Best_Practices_-_Run_Rate___Audio_Good_Video_Not_1_clips"

echo Starting the file renaming and moving process.
echo.
echo Folder 1: %folder1%
echo Folder 2: %folder2%

:: Find the highest number in folder1
set "highest=0"
for %%F in ("%folder1%\clip_*.mp4") do (
    set "fname=%%~nF"
    set "num=!fname:~5!"
    if !num! gtr !highest! set "highest=!num!"
)
echo Highest number found in Folder 1: %highest%

:: Rename and move files from folder2 to folder1
echo Renaming and moving files from Folder 2 to Folder 1...
echo.
for %%F in ("%folder2%\clip_*.mp4") do (
    set /a "highest+=1"
    set "newname=clip_!highest!"
    if !highest! lss 100 set "newname=clip_0!highest!"
    if !highest! lss 10 set "newname=clip_00!highest!"
    echo Moving "%%F" to "%folder1%\!newname!.mp4"
    move "%%F" "%folder1%\!newname!.mp4"
)
echo.
echo File moving complete.

:: Delete folder2 if it's empty
echo Attempting to delete Folder 2...
rmdir "%folder2%" 2>nul
if not exist "%folder2%" (
    echo Folder 2 successfully deleted.
) else (
    echo Could not delete Folder 2. It might not be empty.
)
echo.

echo Task completed.
pause