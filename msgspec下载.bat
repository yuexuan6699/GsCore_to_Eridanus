@echo off
set PYTHON_EXE=..\environments\Python311\python.exe
set PACKAGE=msgspec

rem checking.....
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -m pip install %PACKAGE%
) else (
    echo Python executable not found at: %PYTHON_EXE%
    pause
    exit /b 1
)
pause
