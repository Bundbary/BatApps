@echo off
setlocal enabledelayedexpansion

REM Prompt for the input folder
set /p "folder=Enter the path to the folder containing the files: "

REM Check if the folder exists
if not exist "%folder%" (
    echo The specified folder does not exist.
    goto :eof
)

REM Counter for renamed files
set "renamed_count=0"

REM Loop through all files in the folder
for %%F in ("%folder%\clip_*.json" "%folder%\clip_*.mp3" "%folder%\clip_*.mp4" "%folder%\clip_*.txt") do (
    set "filename=%%~nF"
    set "extension=%%~xF"
    
    echo DEBUG: Processing file: !filename!!extension!
    
    REM Extract the number part
    set "num=!filename:clip_=!"
    
    echo DEBUG: Extracted number: !num!
    
    REM Pad the number to three digits
    set "padded_num=00!num!"
    set "padded_num=!padded_num:~-3!"
    
    echo DEBUG: Padded number: !padded_num!
    
    REM Construct the new filename
    set "new_filename=clip_!padded_num!!extension!"
    
    echo DEBUG: New filename: !new_filename!
    
    REM Rename the file if the new name is different
    if not "!filename!!extension!"=="!new_filename!" (
        ren "%%F" "!new_filename!"
        echo Renamed: !filename!!extension! to !new_filename!
        set /a "renamed_count+=1"
    ) else (
        echo No change needed for: !filename!!extension!
    )
    
    echo.
)

echo.
echo Renaming complete. !renamed_count! file(s) were renamed.
pause