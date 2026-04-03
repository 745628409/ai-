@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0build_windows_exe.ps1" %*
if errorlevel 1 (
  echo [ERROR] Windows 打包失败。
  exit /b 1
)
