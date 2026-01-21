@ECHO OFF
cd %~dp0

ECHO Installing requirements
ECHO python --version
ECHO uv --version
uv sync
PAUSE
