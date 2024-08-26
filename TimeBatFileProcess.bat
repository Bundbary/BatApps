@echo off
setlocal enabledelayedexpansion

REM Check if a file name was provided as a parameter
if "%~1"=="" (
    REM If not, prompt the user for input
    set /p "batch_file=Enter the name of the batch file you want to time: "
) else (
    set "batch_file=%~1"
)

REM Check if the specified file exists
if not exist "!batch_file!" (
    echo Error: The specified file "!batch_file!" does not exist.
    pause
    exit /b 1
)

echo Timing the execution of: !batch_file!

set start=%time%

REM Run the specified batch file
call "!batch_file!"

set end=%time%

REM Convert the time strings to centiseconds
for /F "tokens=1-4 delims=:.," %%a in ("%start%") do (
   set /A "start=(((%%a*60)+1%%b %% 100)*60+1%%c %% 100)*100+1%%d %% 100"
)
for /F "tokens=1-4 delims=:.," %%a in ("%end%") do (
   set /A "end=(((%%a*60)+1%%b %% 100)*60+1%%c %% 100)*100+1%%d %% 100"
)

REM Calculate the elapsed time
set /A elapsed=end-start
set /A hh=elapsed/(60*60*100), rest=elapsed%%(60*60*100), mm=rest/(60*100), rest%%=60*100, ss=rest/100, cc=rest%%100

if %mm% lss 10 set mm=0%mm%
if %ss% lss 10 set ss=0%ss%
if %cc% lss 10 set cc=0%cc%

echo.
echo Execution of "!batch_file!" completed.
echo Time taken: %hh%:%mm%:%ss%.%cc%

pause