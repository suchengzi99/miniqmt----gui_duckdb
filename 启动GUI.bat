@echo off
chcp 65001 >nul
title 沪深A股数据查询系统

echo ========================================
echo    沪深A股数据查询系统
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到Python
    echo 请先安装Python 3.7或更高版本
    echo 下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python环境检测通过
echo.

:: 检查必要文件
if not exist "run_gui.py" (
    echo ❌ 错误：未找到启动文件 run_gui.py
    echo 请确保所有文件都在同一目录下
    echo.
    pause
    exit /b 1
)

if not exist "miniqmt_duckdb.py" (
    echo ❌ 错误：未找到数据库模块 miniqmt_duckdb.py
    echo 请确保所有文件都在同一目录下
    echo.
    pause
    exit /b 1
)

echo ✅ 文件检查通过
echo.

:: 启动GUI
echo 正在启动GUI界面...
echo.
python run_gui.py

:: 如果程序异常退出，显示错误信息
if %errorlevel% neq 0 (
    echo.
    echo ❌ 程序运行出现错误
    echo 请检查：
    echo 1. Python版本是否为3.7+
    echo 2. 是否安装了必要依赖：pandas, duckdb
    echo 3. QMT软件是否已启动
    echo.
    echo 安装依赖命令：
    echo pip install pandas duckdb matplotlib openpyxl
    echo.
)

pause