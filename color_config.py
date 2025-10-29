#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI颜色配置文件
可以在这里自定义界面的颜色方案
"""

# 预设颜色方案
COLOR_SCHEMES = {
    'green': {
        'name': '绿色主题',
        'button_bg': '#4CAF50',
        'button_active': '#45a049',
        'button_pressed': '#3d8b40',
        'select_bg': '#0078d4',
        'bg': '#f0f0f0',
        'fg': '#333333'
    },
    'blue': {
        'name': '蓝色主题',
        'button_bg': '#2196F3',
        'button_active': '#1976D2',
        'button_pressed': '#0D47A1',
        'select_bg': '#0078d4',
        'bg': '#f0f0f0',
        'fg': '#333333'
    },
    'purple': {
        'name': '紫色主题',
        'button_bg': '#9C27B0',
        'button_active': '#7B1FA2',
        'button_pressed': '#4A148C',
        'select_bg': '#0078d4',
        'bg': '#f0f0f0',
        'fg': '#333333'
    },
    'orange': {
        'name': '橙色主题',
        'button_bg': '#FF9800',
        'button_active': '#F57C00',
        'button_pressed': '#E65100',
        'select_bg': '#0078d4',
        'bg': '#f0f0f0',
        'fg': '#333333'
    },
    'red': {
        'name': '红色主题',
        'button_bg': '#F44336',
        'button_active': '#D32F2F',
        'button_pressed': '#B71C1C',
        'select_bg': '#0078d4',
        'bg': '#f0f0f0',
        'fg': '#333333'
    }
}

# 默认使用的颜色方案
DEFAULT_SCHEME = 'green'

def get_color_scheme(scheme_name=None):
    """获取颜色方案"""
    if scheme_name is None:
        scheme_name = DEFAULT_SCHEME
    
    return COLOR_SCHEMES.get(scheme_name, COLOR_SCHEMES[DEFAULT_SCHEME])

def list_color_schemes():
    """列出所有可用的颜色方案"""
    return list(COLOR_SCHEMES.keys())

def get_scheme_names():
    """获取所有颜色方案的显示名称"""
    return {name: config['name'] for name, config in COLOR_SCHEMES.items()}

if __name__ == "__main__":
    # 测试颜色方案
    print("可用的颜色方案:")
    for name, config in COLOR_SCHEMES.items():
        print(f"  {name}: {config['name']}")
    
    print(f"\n默认方案: {DEFAULT_SCHEME}")
    print(f"默认方案详情: {get_color_scheme()}")