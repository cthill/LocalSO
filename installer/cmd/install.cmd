@echo off
echo This script will modify %WINDIR%\System32\drivers\etc\hosts so that you can connect to LocalSO. A backup will be made.
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

    type %WINDIR%\System32\drivers\etc\hosts | find /v "stickonline.redirectme.net" | find /v "stick-online.com" > %WINDIR%\System32\drivers\etc\hosts_new

    echo adding hosts file entry 127.0.0.1 stickonline.redirectme.net
    echo. >> %WINDIR%\System32\drivers\etc\hosts_new
    echo 127.0.0.1 stickonline.redirectme.net >> %WINDIR%\System32\drivers\etc\hosts_new

    echo adding hosts file entry 127.0.0.1 stick-online.com
    echo 127.0.0.1 stick-online.com >> %WINDIR%\System32\drivers\etc\hosts_new

    echo adding hosts file entry 127.0.0.1 www.stick-online.com
    echo 127.0.0.1 www.stick-online.com >> %WINDIR%\System32\drivers\etc\hosts_new

    type %WINDIR%\System32\drivers\etc\hosts_new > %WINDIR%\System32\drivers\etc\hosts
    del %WINDIR%\System32\drivers\etc\hosts_new

    echo.
    echo Done! You can now launch StickOnline.exe
    echo.
) else (
    echo.
    echo ERROR! This script must be run as administrator
    echo Please right-click this script and select 'Run as Administrator'
    echo.
)

:END
pause
