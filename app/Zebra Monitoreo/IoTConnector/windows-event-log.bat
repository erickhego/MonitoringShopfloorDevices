:: Add IoTConnector as a subkey under EventLog\Application
@echo off
goto check_Permissions

:check_Permissions
	::Check and acquire admin rights
	net session >nul 2>&1
	if %errorLevel% == 0 (
		goto :usercode
	) else (
		echo Run this file with admin rights.
		MSHTA "javascript: var shell = new ActiveXObject('shell.application'); shell.ShellExecute("%~snx0", 'UAC', '', 'runas', 1);close();")
	)

	:: Recheck admin rights
	net session >nul 2>&1
	if %errorLevel% == 0 (
		goto :usercode
	) else (
		goto :end
	)

:usercode
	REG ADD "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\EventLog\Application\IoT Connector" /v "TypesSupported" /t REG_DWORD /d 7
	REG ADD "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\EventLog\Application\IoT Connector" /v "EventMessageFile" /t REG_SZ /d "%~dp0windows_message_text.dll"

:end
	exit /b 