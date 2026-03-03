@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

echo == Instalador Windows ==
echo Proyecto: %CD%

call :find_python
if not defined PY_EXE (
  echo [INFO] Python no encontrado. Intentando instalar con winget...
  call :install_python
  call :refresh_path
  call :find_python
)

if not defined PY_EXE (
  echo [ERROR] No se pudo instalar Python automaticamente.
  echo Instala Python 3.11+ y vuelve a ejecutar este instalador.
  pause
  exit /b 1
)

echo [INFO] Usando Python: %PY_EXE% %PY_SWITCH%

call :install_mpg123

if not exist ".venv" (
  echo [INFO] Creando entorno virtual...
  call :run_python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
  )
)

set "VENV_PY=.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [ERROR] No se encontro %VENV_PY%
  pause
  exit /b 1
)

echo [INFO] Instalando dependencias Python...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto :pip_error
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :pip_error
"%VENV_PY%" -m pip install edge-tts
if errorlevel 1 goto :pip_error

echo.
echo Instalacion terminada.
set /p OPEN_APP=Quieres abrir la app ahora? [S/n]:
if /I "%OPEN_APP%"=="" set "OPEN_APP=S"
if /I "%OPEN_APP%"=="S" "%VENV_PY%" -m src.infrastructure.gui_main

pause
exit /b 0

:pip_error
echo [ERROR] Fallo instalando dependencias Python.
echo Revisa conexion a internet y vuelve a ejecutar el instalador.
pause
exit /b 1

:find_python
set "PY_EXE="
set "PY_SWITCH="
where py >nul 2>&1
if not errorlevel 1 (
  set "PY_EXE=py"
  set "PY_SWITCH=-3"
  exit /b 0
)
where python >nul 2>&1
if not errorlevel 1 (
  set "PY_EXE=python"
  set "PY_SWITCH="
)
exit /b 0

:run_python
if defined PY_SWITCH (
  %PY_EXE% %PY_SWITCH% %*
) else (
  %PY_EXE% %*
)
exit /b %errorlevel%

:install_python
where winget >nul 2>&1
if errorlevel 1 (
  echo [WARN] winget no esta disponible, no se puede autoinstalar Python.
  exit /b 1
)
winget install --exact --id Python.Python.3.11 --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
  winget install --exact --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
)
exit /b 0

:install_mpg123
where winget >nul 2>&1
if errorlevel 1 (
  echo [WARN] winget no disponible. Instala mpg123 manualmente y agregalo al PATH.
  exit /b 0
)
echo [INFO] Intentando instalar mpg123...
winget install --exact --id Mpg123.mpg123 --accept-source-agreements --accept-package-agreements >nul 2>&1
if errorlevel 1 (
  winget install --exact --id mpg123.mpg123 --accept-source-agreements --accept-package-agreements >nul 2>&1
)
if errorlevel 1 (
  echo [WARN] No se pudo instalar mpg123 automaticamente.
  echo [WARN] Instala mpg123 manualmente y agregalo al PATH.
)
exit /b 0

:refresh_path
set "PATH=%PATH%;%LocalAppData%\Programs\Python\Python311;%LocalAppData%\Programs\Python\Python311\Scripts"
set "PATH=%PATH%;%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts"
set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"
set "PATH=%PATH%;C:\Program Files\Python312;C:\Program Files\Python312\Scripts"
exit /b 0
