@echo off
REM ============================================================================
REM T14 Map Explorer - Streamlit Runner
REM ============================================================================
REM This script starts the Streamlit application
REM ============================================================================

setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "PY_CMD="
set "CURRENT_PY_VERSION="
set "PREV_VENV_VERSION="
set "RECREATE_REASON="
set "FORCE_FRESH=0"
set "FORCE_SYNC=0"
set "NEED_REBUILD=0"
set "NEED_SYNC=0"

if /i "%~1"=="--fresh" set "FORCE_FRESH=1"
if /i "%~1"=="fresh" set "FORCE_FRESH=1"
if /i "%~1"=="--sync" set "FORCE_SYNC=1"
if /i "%~1"=="sync" set "FORCE_SYNC=1"

where py >nul 2>nul
if %errorlevel%==0 (
	set "PY_CMD=py"
) else (
	where python >nul 2>nul
	if %errorlevel%==0 (
		set "PY_CMD=python"
	)
)

if "%PY_CMD%"=="" (
	echo [ERROR] Python launcher was not found. Install Python and add it to PATH.
	goto :fail
)

for /f "tokens=2" %%v in ('%PY_CMD% -V 2^>^&1') do set "CURRENT_PY_VERSION=%%v"
if "%CURRENT_PY_VERSION%"=="" (
	echo [ERROR] Could not determine current Python version.
	goto :fail
)

echo [INFO] Current Python version: %CURRENT_PY_VERSION%

if exist "%VENV_DIR%\pyvenv.cfg" (
	for /f "tokens=3" %%v in ('findstr /b /i "version" "%VENV_DIR%\pyvenv.cfg"') do set "PREV_VENV_VERSION=%%v"
	if not "%PREV_VENV_VERSION%"=="" (
		echo [INFO] Existing venv Python version: %PREV_VENV_VERSION%
	)
) else (
	echo [INFO] No existing virtual environment metadata found.
)

if "%PREV_VENV_VERSION%"=="" (
	set "RECREATE_REASON=No existing virtual environment detected."
	set "NEED_REBUILD=1"
) else (
	if /i "%PREV_VENV_VERSION%"=="%CURRENT_PY_VERSION%" (
		set "RECREATE_REASON=Python version unchanged; existing environment can be reused."
	) else (
		set "RECREATE_REASON=Python version changed; rebuilding environment to match the new interpreter."
		set "NEED_REBUILD=1"
	)
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
	set "RECREATE_REASON=Virtual environment is incomplete or missing. Rebuilding."
	set "NEED_REBUILD=1"
)

if "%FORCE_FRESH%"=="1" (
	set "RECREATE_REASON=--fresh requested; rebuilding environment from scratch."
	set "NEED_REBUILD=1"
)

if "%FORCE_SYNC%"=="1" (
	set "NEED_SYNC=1"
)

echo [INFO] %RECREATE_REASON%

if "%NEED_REBUILD%"=="1" (
	if exist "%VENV_DIR%" (
		echo [INFO] Deleting existing virtual environment...
		rmdir /s /q "%VENV_DIR%"
		if errorlevel 1 (
			echo [ERROR] Failed to delete existing virtual environment.
			goto :fail
		)
	)

 	echo [INFO] Creating virtual environment...
	%PY_CMD% -m venv "%VENV_DIR%"
	if errorlevel 1 (
		echo [ERROR] Failed to create virtual environment.
		goto :fail
	)

 	echo [INFO] Upgrading pip...
	"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
	if errorlevel 1 (
		echo [ERROR] Failed to upgrade pip.
		goto :fail
	)

	 echo [INFO] Installing dependencies from requirements.txt...
	"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
	if errorlevel 1 (
		echo [ERROR] Failed to install dependencies.
		goto :fail
	)
) else (
	echo [INFO] Reusing existing virtual environment. Use --fresh to rebuild.
	if "%NEED_SYNC%"=="1" (
		echo [INFO] --sync requested; installing dependencies from requirements.txt...
		"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
		if errorlevel 1 (
			echo [ERROR] Failed to install dependencies.
			goto :fail
		)
	)
)

echo [INFO] Starting Streamlit app...
"%VENV_DIR%\Scripts\streamlit.exe" run app.py
set "APP_EXIT_CODE=%errorlevel%"

echo.
echo [INFO] Streamlit process exited with code %APP_EXIT_CODE%.
echo [INFO] Terminal kept open for troubleshooting.
pause
exit /b %APP_EXIT_CODE%

:fail
echo.
echo [INFO] Startup failed. Review errors above.
echo [INFO] Terminal kept open for troubleshooting.
pause
exit /b 1
