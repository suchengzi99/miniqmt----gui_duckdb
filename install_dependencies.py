#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖项安装脚本
"""

import subprocess
import sys
import os

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {package} 安装失败")
        return False

def check_package(package):
    """检查包是否已安装"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    """主函数"""
    print("=== 沪深A股数据查询系统 - 依赖项安装 ===")
    print()
    
    # 检查pip是否可用
    try:
        import pip
        print("✅ pip 可用")
    except ImportError:
        print("❌ pip 不可用，请先安装pip")
        input("按回车键退出...")
        sys.exit(1)
    
    print()
    
    # 必要依赖项
    required_packages = [
        ("pandas", "数据处理库"),
        ("duckdb", "数据库库"),
    ]
    
    # 可选依赖项
    optional_packages = [
        ("matplotlib", "图表绘制库"),
        ("openpyxl", "Excel文件支持"),
    ]
    
    print("正在检查必要依赖项...")
    print()
    
    # 安装必要依赖项
    failed_required = []
    for package, description in required_packages:
        print(f"检查 {package} ({description})...")
        if check_package(package):
            print(f"✅ {package} 已安装")
        else:
            print(f"⬇️  正在安装 {package}...")
            if not install_package(package):
                failed_required.append(package)
        print()
    
    # 检查必要依赖项是否全部安装成功
    if failed_required:
        print("❌ 以下必要依赖项安装失败:")
        for package in failed_required:
            print(f"   - {package}")
        print()
        print("请手动安装这些依赖项或检查网络连接")
        input("按回车键退出...")
        sys.exit(1)
    
    print("✅ 所有必要依赖项已安装完成")
    print()
    
    # 安装可选依赖项
    print("正在检查可选依赖项...")
    print()
    
    for package, description in optional_packages:
        print(f"检查 {package} ({description})...")
        if check_package(package):
            print(f"✅ {package} 已安装")
        else:
            print(f"⬇️  正在安装 {package}...")
            install_package(package)  # 可选依赖项安装失败不影响使用
        print()
    
    print("🎉 依赖项安装完成！")
    print()
    print("现在可以运行以下命令启动GUI:")
    print("  python run_gui.py")
    print("  或双击 '启动GUI.bat'")
    print()
    
    # 检查QMT相关文件
    print("正在检查QMT相关文件...")
    qmt_files = [
        "miniqmt_duckdb.py",
        "stock_gui_improved.py",
        "stock_gui_simple.py",
        "run_gui.py"
    ]
    
    missing_files = []
    for file in qmt_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} 缺失")
            missing_files.append(file)
    
    if missing_files:
        print()
        print("⚠️  以下文件缺失，可能影响程序运行:")
        for file in missing_files:
            print(f"   - {file}")
        print()
        print("请确保所有程序文件都在同一目录下")
    
    print()
    input("按回车键退出...")

if __name__ == "__main__":
    main()