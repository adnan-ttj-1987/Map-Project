@echo off
REM ============================================================================
REM T14 Map Explorer - Streamlit Runner
REM ============================================================================
REM This script starts the Streamlit application
REM ============================================================================

cd /d "C:\Users\Documents\map-project"

REM Activate virtual environment
call Scripts\activate.bat

REM Run Streamlit app
streamlit run app.py

pause
