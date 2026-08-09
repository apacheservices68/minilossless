@echo off
REM Script to run pytest unit tests on Windows
set PYTHONPATH=.
pytest -v tests/
pause
