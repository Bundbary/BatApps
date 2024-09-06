@echo off
set /p folder="Enter the folder path: "
set /p output="Enter the output file path (e.g., C:\output.txt): "
dir /s /b "%folder%" > "%output%"
echo File list has been written to %output%