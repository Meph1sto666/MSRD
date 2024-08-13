@ECHO OFF
cd %~dp0
if not exist .\venv (
	ECHO CREATING VIRTUAL ENVIRONMENT
	python -m venv venv
)
CALL venv\Scripts\activate

ECHO Installing requirements
ECHO python --version
pip install -r requirements.txt
PAUSE