@echo off
chcp 65001 > nul
echo ========================================================
echo  KHOI DONG FRONTEND - ENTERPRISE RAG WORKSPACE
echo ========================================================
echo.

call venv\Scripts\activate.bat

echo Dang mo giao dien web tai: http://localhost:8501
echo.
streamlit run frontend/app.py --server.port 8501
pause
