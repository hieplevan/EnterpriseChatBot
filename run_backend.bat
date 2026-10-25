@echo off
chcp 65001 > nul
echo ========================================================
echo  KHOI DONG BACKEND FASTAPI - ADVANCED RAG ENGINE
echo ========================================================
echo.

set OLLAMA_VULKAN=false
set CUDA_VISIBLE_DEVICES=-1

call venv\Scripts\activate.bat

echo Dang chay FastAPI backend tai: http://127.0.0.1:8000
echo Swagger API Docs tai: http://127.0.0.1:8000/docs
echo.
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
