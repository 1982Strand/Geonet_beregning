@echo off
:: Skift til den mappe, hvor denne .bat-fil ligger
cd /d "%~dp0"

:: Tjek at det virtuelle miljoe findes
if not exist ".venv\Scripts\python.exe" (
    echo .venv blev ikke fundet i denne mappe.
    echo Opret den med:  py -3.12 -m venv .venv ^&^& .venv\Scripts\python -m pip install -r requirements.txt
    pause
    exit /b 1
)

:: Start browseren manuelt i baggrunden (hvis Streamlit mod forventning ikke goer det selv)
start "" "http://localhost:8501"

:: Start streamlit via venv'ens python (ikke den globale)
".venv\Scripts\python.exe" -m streamlit run app.py

pause
