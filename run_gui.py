#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沪深A股数据查询系统启动脚本
"""

import sys
import os

def check_dependencies():
    """检查必要的依赖项"""
    required_modules = [
        'tkinter',
        'pandas',
        'duckdb',
        'xtquant'
    ]
    
    optional_modules = [
        'matplotlib',
        'openpyxl'
    ]
    
    missing_required = []
    missing_optional = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_required.append(module)
    
    for module in optional_modules:
        try:
            __import__(module)
        except ImportError:
            missing_optional.append(module)
    
    if missing_required:
        print("❌ 缺少必要的依赖项:")
        for module in missing_required:
            print(f"   - {module}")
        print("\n请安装缺少的依赖项后重试")
        return False
    
    if missing_optional:
        print("⚠️  缺少可选依赖项(部分功能可能不可用):")
        for module in missing_optional:
            print(f"   - {module}")
        print("\n建议安装: pip install matplotlib openpyxl")
    
    return True

def main():
    """主函数"""
    print("=== 沪深A股数据查询系统 ===")
    print("正在检查依赖项...")
    
    if not check_dependencies():
        input("按回车键退出...")
        sys.exit(1)
    
    print("✅ 依赖项检查通过")
    print("正在启动GUI界面...")
    
    try:
        # 尝试导入并启动完整版GUI
        try:
            from stock_gui_improved import ModernStockGUI
            print("启动完整版界面(包含图表功能)...")
            app_class = ModernStockGUI
        except ImportError as e:
            print(f"完整版界面启动失败: {e}")
            print("启动简化版界面...")
            from stock_gui_simple import SimpleStockGUI
            app_class = SimpleStockGUI
        
        import tkinter as tk
        
        root = tk.Tk()
        app = app_class(root)
        
        # 处理窗口关闭事件
        def on_closing():
            if hasattr(app, 'db') and app.db:
                app.db.close()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        print("✅ GUI界面启动成功")
        print("\n💡 提示：运行 'python color_chooser.py' 可以自定义按钮颜色")
        root.mainloop()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请检查错误信息并重试")
        input("按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()