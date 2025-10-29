#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
颜色选择器工具
用于选择和预览不同的按钮颜色方案nnn
"""

import tkinter as tk
from tkinter import ttk, messagebox
from color_config import COLOR_SCHEMES, get_color_scheme, get_scheme_names

class ColorChooser:
    def __init__(self, root):
        self.root = root
        self.root.title("按钮颜色选择器")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # 当前选择的颜色方案
        self.current_scheme = tk.StringVar(value="green")
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="选择按钮颜色主题", 
                             font=('Microsoft YaHei', 12, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 颜色方案选择
        scheme_frame = ttk.LabelFrame(main_frame, text="颜色方案", padding="10")
        scheme_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 获取颜色方案列表
        scheme_names = get_scheme_names()
        
        # 创建单选按钮
        for i, (key, name) in enumerate(scheme_names.items()):
            ttk.Radiobutton(scheme_frame, text=name, variable=self.current_scheme, 
                           value=key, command=self.update_preview).pack(
                               anchor=tk.W, pady=2)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 创建预览按钮
        self.preview_buttons = []
        button_texts = ["查询数据", "导出数据", "刷新", "清空"]
        
        for i, text in enumerate(button_texts):
            btn = tk.Button(preview_frame, text=text, width=15, height=2)
            btn.grid(row=i//2, column=i%2, padx=10, pady=5)
            self.preview_buttons.append(btn)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 应用按钮
        apply_btn = ttk.Button(button_frame, text="应用颜色", command=self.apply_colors)
        apply_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        cancel_btn = ttk.Button(button_frame, text="取消", command=self.root.destroy)
        cancel_btn.pack(side=tk.LEFT)
        
        # 初始化预览
        self.update_preview()
        
    def update_preview(self):
        """更新预览"""
        scheme_name = self.current_scheme.get()
        color_scheme = get_color_scheme(scheme_name)
        
        # 更新预览按钮的颜色
        for btn in self.preview_buttons:
            btn.configure(
                bg=color_scheme['button_bg'],
                activebackground=color_scheme['button_active'],
                fg='white',
                font=('Microsoft YaHei', 9)
            )
    
    def apply_colors(self):
        """应用颜色设置"""
        scheme_name = self.current_scheme.get()
        color_scheme = get_color_scheme(scheme_name)
        
        # 更新配置文件中的默认方案
        try:
            with open('color_config.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换默认方案
            content = content.replace(
                "DEFAULT_SCHEME = 'green'",
                f"DEFAULT_SCHEME = '{scheme_name}'"
            )
            
            with open('color_config.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            messagebox.showinfo("成功", 
                             f"已应用 {color_scheme['name']}\n\n"
                             f"重启GUI后生效")
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"应用颜色失败: {e}")

def main():
    root = tk.Tk()
    app = ColorChooser(root)
    root.mainloop()

if __name__ == "__main__":
    main()