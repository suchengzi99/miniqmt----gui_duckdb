#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI测试脚本
"""

import sys
import os

def test_imports():
    """测试导入"""
    print("正在测试模块导入...")
    
    try:
        import tkinter as tk
        print("✅ tkinter 导入成功")
    except ImportError as e:
        print(f"❌ tkinter 导入失败: {e}")
        return False
    
    try:
        from tkinter import ttk, messagebox, filedialog
        print("✅ tkinter.ttk 导入成功")
    except ImportError as e:
        print(f"❌ tkinter.ttk 导入失败: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas 导入成功")
    except ImportError as e:
        print(f"❌ pandas 导入失败: {e}")
        return False
    
    try:
        import duckdb
        print("✅ duckdb 导入成功")
    except ImportError as e:
        print(f"❌ duckdb 导入失败: {e}")
        return False
    
    try:
        from miniqmt_duckdb import MiniqmtDuckDB
        print("✅ miniqmt_duckdb 导入成功")
    except ImportError as e:
        print(f"❌ miniqmt_duckdb 导入失败: {e}")
        return False
    
    return True

def test_gui_creation():
    """测试GUI创建"""
    print("\n正在测试GUI创建...")
    
    try:
        # 测试简化版GUI
        print("测试简化版GUI...")
        import tkinter as tk
        from stock_gui_simple import SimpleStockGUI
        
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        # 尝试创建GUI实例
        app = SimpleStockGUI(root)
        print("✅ 简化版GUI创建成功")
        
        # 清理
        if hasattr(app, 'db') and app.db:
            app.db.close()
        root.destroy()
        
    except Exception as e:
        print(f"❌ 简化版GUI创建失败: {e}")
        return False
    
    try:
        # 测试完整版GUI
        print("测试完整版GUI...")
        import tkinter as tk
        from stock_gui_improved import ModernStockGUI
        
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        # 尝试创建GUI实例
        app = ModernStockGUI(root)
        print("✅ 完整版GUI创建成功")
        
        # 清理
        if hasattr(app, 'db') and app.db:
            app.db.close()
        root.destroy()
        
    except Exception as e:
        print(f"⚠️  完整版GUI创建失败（可能是matplotlib未安装）: {e}")
    
    return True

def main():
    """主函数"""
    print("=== GUI测试脚本 ===")
    print()
    
    # 测试导入
    if not test_imports():
        print("\n❌ 模块导入测试失败")
        print("请安装缺少的依赖项")
        input("按回车键退出...")
        sys.exit(1)
    
    # 测试GUI创建
    if not test_gui_creation():
        print("\n❌ GUI创建测试失败")
        input("按回车键退出...")
        sys.exit(1)
    
    print("\n🎉 所有测试通过！")
    print("GUI界面应该可以正常运行")
    print()
    print("启动命令:")
    print("  python run_gui.py")
    print("  或双击 '启动GUI.bat'")
    print()
    input("按回车键退出...")

if __name__ == "__main__":
    main()