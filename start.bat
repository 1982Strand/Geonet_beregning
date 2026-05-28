@echo off
:: Skift til den mappe, hvor denne .bat-fil ligger
cd /d "%~dp0"

:: Start browseren manuelt i baggrunden (hvis Streamlit mod forventning ikke gør det selv)
start "" "http://localhost:8501"

:: Start streamlit direkte
python -m streamlit run app.py

pause