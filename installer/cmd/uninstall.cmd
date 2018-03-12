@echo off
echo This script will modify %WINDIR%\System32\drivers\etc\hosts. A backup will be made.
echo.
SET AREYOUSURE=N
:PROMPT
SET /P AREYOUSURE=Do you want to continue(Y/[N])?
IF /I "%AREYOUSURE%" NEQ "Y" GOTO END

echo.
echo Checking administrator privileges...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Creating backup file %WINDIR%\System32\drivers\etc\hosts.bak
    copy %WINDIR%\System32\drivers\etc\hosts %WINDIR%\System32\drivers\etc\hosts.bak > nul

    echo Removing hosts file entires for stickonline.redirectme.net and stick-online.com
    type %WINDIR%\System32\drivers\etc\hosts | find /v "stickonline.redirectme.net" | find /v "stick-online.com" > %WINDIR%\System32\drivers\etc\hosts_new
    type %WINDIR%\System32\drivers\etc\hosts_new > %WINDIR%\System32\drivers\etc\hosts
    del %WINDIR%\System32\drivers\etc\hosts_new

    echo.
    echo Done!
    echo.
) else (
    echo.
    echo ERROR! This script must be run as administrator
    echo Please right-click this script and select 'Run as Administrator'
    echo.
)

:END
pause
