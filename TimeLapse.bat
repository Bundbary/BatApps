
@echo off
setlocal enabledelayedexpansion

:: Start time for time lapse
for /f "tokens=1-4 delims=:.," %%a in ("%time%") do (
    set /a "start=(((%%a*60+1%%b%%100)*60+1%%c%%100)*100+1%%d%%100)-36610100"
)

:: Simulate some work with a delay (e.g., pinging localhost)
ping -n 3 127.0.0.1 >nul

:: End time for time lapse
for /f "tokens=1-4 delims=:.," %%a in ("%time%") do (
    set /a "end=(((%%a*60+1%%b%%100)*60+1%%c%%100)*100+1%%d%%100)-36610100"
)

:: Calculate the duration
set /a duration=end-start
echo Duration: !duration!
pause

endlocal