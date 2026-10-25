@echo off
set OLLAMA_VULKAN=false
set CUDA_VISIBLE_DEVICES=-1
"%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
