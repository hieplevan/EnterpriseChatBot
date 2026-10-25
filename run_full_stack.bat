@echo off
chcp 65001 > nul
echo ========================================================
echo  KHOI DONG FULL STACK RAG (FASTAPI BACKEND + FRONTEND)
echo ========================================================
echo.

set OLLAMA_VULKAN=false
set CUDA_VISIBLE_DEVICES=-1

echo 1. Khoi dong FastAPI Backend tren cong 8000...
start "RAG Backend (FastAPI)" cmd /c "call run_backend.bat"

timeout /t 2 /nobreak > nul

echo 2. Khoi dong Streamlit Frontend tren cong 8501...
start "RAG Frontend (Claude Code)" cmd /c "call run_frontend.bat"

echo.
echo He thong dang khoi chay!
echo - API Docs: http://127.0.0.1:8000/docs
echo - Web App:  http://localhost:8501
echo.
