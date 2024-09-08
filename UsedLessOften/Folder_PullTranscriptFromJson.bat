@echo off
setlocal enabledelayedexpansion


REM Check if jq is installed
where jq >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: jq is not installed or not in the system PATH.
    echo Please install jq from https://stedolan.github.io/jq/download/
    echo and add it to your system PATH.
    goto :end
)

REM Confirmation prompt
set /p "confirm=Press Y if you ran this file on purpose. (Y/N): "
if /i "%confirm%" neq "Y" goto :end

REM Get folder path from user
set /p "input_folder=Enter the path to the folder containing JSON files: "

REM Check if the folder exists
if not exist "%input_folder%" (
    echo Error: The specified folder does not exist.
    goto :end
)

echo Processing files in: %input_folder%

REM Process each JSON file in the folder
for %%F in ("%input_folder%\*.json") do (
    echo Processing file: %%F
    set "output_file=%%~nF_transcript.txt"
    set "output_file=!output_file:.mp4=!"
    set "full_output_path=!input_folder!\!output_file!"
    
    jq -r ".transcript[-1].text" "%%F" > "!full_output_path!"
    
    if errorlevel 1 (
        echo Error processing %%F
    ) else (
        echo Transcript saved to: !full_output_path!
    )
    echo.
)

echo Processing complete. 
echo Transcript files should have been saved in: %input_folder%
echo List of files in the output folder:
dir /b "%input_folder%\*_transcript.txt"

:end
echo.
echo Press any key to exit...
pause >nul

endlocal