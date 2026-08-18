@echo off
:: Skift til den mappe, hvor denne .bat-fil ligger
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto :start

:: Foerste gang paa denne maskine: opret .venv og installer paakraevede
:: pakker automatisk. Kolleger skal derfor kun have Python 3.12 installeret
:: paa forhaand -- resten klarer denne fil, saa opsaetningen ikke kraever
:: en terminal.
echo .venv blev ikke fundet -- opretter den foerste gang. Det tager et par minutter.
echo.

where py >nul 2>nul
if errorlevel 1 goto :ingen_python

py -3.12 -m venv .venv
if errorlevel 1 goto :venv_fejl

echo Installerer paakraevede pakker...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :pip_fejl

echo.
echo Opsaetning fuldfoert.
echo.

:start
:: Start browseren manuelt i baggrunden (hvis Streamlit mod forventning ikke goer det selv)
start "" "http://localhost:8501"

:: Start streamlit via venv'ens python (ikke den globale)
".venv\Scripts\python.exe" -m streamlit run app.py

pause
exit /b 0

:ingen_python
echo.
echo Python blev ikke fundet paa denne maskine.
echo Installer Python 3.12 fra https://www.python.org/downloads/
echo Husk at markere "Add python.exe to PATH" under installationen.
echo Koer derefter denne fil igen.
pause
exit /b 1

:venv_fejl
echo.
echo Kunne ikke oprette .venv med Python 3.12 -- er den installeret?
echo Installer den fra https://www.python.org/downloads/ og proev igen.
pause
exit /b 1

:pip_fejl
echo.
echo Installation af paakraevede pakker fejlede -- se fejlen ovenfor.
echo Tjek internetforbindelsen og proev igen. Hjaelper det ikke, saa slet
echo mappen .venv og koer denne fil igen for at starte forfra.
pause
exit /b 1
