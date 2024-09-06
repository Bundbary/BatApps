@echo off
setlocal enabledelayedexpansion

:: Set the path to your local directory
set "LOCAL_DIR=c:\Users\bpenn\ExpectancyLearning\flask_apps\VideoTranscriptEditor\static\video_library"

:: Set the path to your SharePoint export CSV
set "SHAREPOINT_CSV=c:\Users\bpenn\Downloads\SPFiles.csv"



:: Create result files in the same directory as the batch file
set "MISSING_LOCAL=%~dp0missing_in_local.txt"
set "MISSING_SHAREPOINT=%~dp0missing_in_sharepoint.txt"

:: Create temporary files
set "LOCAL_LIST=%TEMP%\local_files.txt"
set "SP_LIST=%TEMP%\sp_files.txt"

echo Generating list of local files...
dir /b /s "%LOCAL_DIR%" > "%LOCAL_LIST%"
echo Done.

echo Extracting SharePoint filenames...
for /f "skip=1 usebackq tokens=2 delims=," %%a in ("%SHAREPOINT_CSV%") do (
    echo %%~nxa >> "%SP_LIST%"
)
echo Done.

echo Counting files...
for /f %%a in ('type "%LOCAL_LIST%" ^| find /c /v ""') do set LOCAL_COUNT=%%a
for /f %%a in ('type "%SP_LIST%" ^| find /c /v ""') do set SP_COUNT=%%a
echo Local files: %LOCAL_COUNT%
echo SharePoint files: %SP_COUNT%
echo.

echo Comparing files (this may take a while)...
findstr /vixg:"%SP_LIST%" "%LOCAL_LIST%" > "%MISSING_SHAREPOINT%"
findstr /vixg:"%LOCAL_LIST%" "%SP_LIST%" > "%MISSING_LOCAL%"
echo Comparison complete.
echo.

echo Results saved to:
echo %MISSING_LOCAL%
echo %MISSING_SHAREPOINT%
echo.

echo Files in SharePoint but missing locally:
type "%MISSING_LOCAL%"
echo.
echo Files locally but missing in SharePoint:
type "%MISSING_SHAREPOINT%"

echo.
echo Cleaning up temporary files...
del "%LOCAL_LIST%" "%SP_LIST%"
echo Done.

pause