@echo off
setlocal enabledelayedexpansion

:: Check if jq is available
where jq >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: jq is not found. Please ensure it's installed and in your PATH.
    pause
    exit /b 1
)

:: Create output folder
if not exist "output" mkdir "output"

:: Initialize counter
set /a counter=0

:: Get folder paths from user
set /p "folders=Enter comma-separated folder paths: "

:: Loop through each folder
for %%F in (%folders%) do (
    :: Check if the folder exists
    if exist "%%~F" (
        echo Processing folder: %%F
        :: Process each MP4 file in the folder
        for %%G in ("%%~F\*.mp4") do (
            :: Format the counter with leading zeros
            set "formatted_counter=000!counter!"
            set "formatted_counter=!formatted_counter:~-3!"
            
            :: Copy and rename the MP4 file
            echo Original MP4: %%G
            echo New MP4: output\clip_!formatted_counter!.mp4
            copy "%%G" "output\clip_!formatted_counter!.mp4"
            
            :: Get the base name of the original file (without extension)
            for %%H in ("%%~nG") do set "baseName=%%~nH"
            
            :: Check for and copy associated files
            for %%I in (json txt srt) do (
                if exist "%%~dpG!baseName!.%%I" (
                    echo Original %%I: %%~dpG!baseName!.%%I
                    echo New %%I: output\clip_!formatted_counter!.%%I
                    
                    :: Special handling for JSON files
                    if "%%I"=="json" (
                        :: Use jq to update the "label" field and save to a temporary file
                        jq ".label = \"clip_!formatted_counter!\"" "%%~dpG!baseName!.%%I" > "output\temp.json"
                        :: Move the temporary file to the final destination
                        move /Y "output\temp.json" "output\clip_!formatted_counter!.%%I" >nul
                    ) else (
                        :: For non-JSON files, just copy
                        copy "%%~dpG!baseName!.%%I" "output\clip_!formatted_counter!.%%I"
                    )
                )
            )
            
            echo.
            set /a counter+=1
        )
    ) else (
        echo Folder not found: %%F
    )
)

:: Clean up any remaining temporary file
if exist "output\temp.json" del "output\temp.json"

echo File renaming, copying, and JSON editing complete. Files are in the 'output' folder.
echo Total MP4 files processed: %counter%
pause