@echo off

:check
(
    python -h >nul 2>nul
) || (
    goto err
)

:ok
python .\src\main.py %*
exit

:err
echo You have to download Python 2.x.x to start CBT.
echo If you have already downloaded Python, add
echo Python directory to %%PATH%%.
echo Would you like to add it now?
set /p response=[y - yes, n - no]: 
if %response%==y (
    goto add
)
exit

:add
set /p newpath=Enter Python 2.x.x path: 
if not exist %newpath%\python.exe (
    echo This path is incorrect.
    goto add
)
setx path "%path%;%newpath%"
goto ok