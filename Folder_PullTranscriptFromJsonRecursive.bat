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
set /p "confirm=Press Y if you want to recursively process JSON files in a folder. (Y/N): "
if /i "%confirm%" neq "Y" goto :end

REM Get folder path from user
set /p "root_folder=Enter the path to the root folder containing JSON files: "

REM Check if the folder exists
if not exist "%root_folder%" (
    echo Error: The specified folder does not exist.
    goto :end
)

echo Processing files in: %root_folder%

REM Call the recursive function
call :ProcessFolder "%root_folder%"

echo Processing complete.
goto :end

:ProcessFolder
setlocal
set "current_folder=%~1"

REM Process each JSON file in the current folder
for %%F in ("%current_folder%\*.json") do (
    echo Processing file: %%F
    set "output_file=%%~nF_transcript.txt"
    set "output_file=!output_file:.mp4=!"
    set "full_output_path=!current_folder!\!output_file!"
    
    jq -r ".transcript[-1].text" "%%F" > "!full_output_path!"
    
    if errorlevel 1 (
        echo Error processing %%F
    ) else (
        echo Transcript saved to: !full_output_path!
    )
    echo.
)

REM Recursively process subfolders, skipping those with 'backup' in the name
for /d %%D in ("%current_folder%\*") do (
    set "folder_name=%%~nxD"
    echo !folder_name! | findstr /i "backup" >nul
    if errorlevel 1 (
        call :ProcessFolder "%%D"
    ) else (
        echo Skipping backup folder: %%D
    )
)

endlocal
exit /b

:end
echo.
echo Press any key to exit...
pause >nul

endlocal