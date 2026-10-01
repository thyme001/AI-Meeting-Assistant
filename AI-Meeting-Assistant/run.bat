@echo off
cd /d "%~dp0"
cls
echo Starting AI Meeting Assistant...
echo.
echo Using local port: 8502
echo.
"C:\Users\ASUS\anaconda3\python.exe" -m streamlit run app.py --server.port 8502

echo.
echo Streamlit process exited. Press any key to close this window...
pause >nul
