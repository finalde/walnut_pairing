#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文玩核桃配对 - 自动文件夹创建脚本
首次运行时自动创建必要的文件夹结构
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

def create_necessary_folders():
    """创建必要的文件夹结构"""
    try:
        # 获取可执行文件所在目录
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件
            base_dir = Path(sys.executable).parent
        else:
            # 开发环境
            base_dir = Path(__file__).parent
        
        # 创建数据库目录结构
        database_dir = base_dir / 'walnut_database'
        crop_dir = database_dir / 'crop_images'
        
        # 创建目录
        database_dir.mkdir(exist_ok=True)
        crop_dir.mkdir(exist_ok=True)
        
        # 创建说明文件
        readme_path = database_dir / 'README.txt'
        if not readme_path.exists():
            readme_text = """文玩核桃配对 - 数据目录说明

此目录用于存储程序运行过程中生成的数据：
- crop_images/: 存储裁剪后的核桃图像
- tensor_features_cache.pkl: 特征缓存文件（自动生成）
- cache_validation_log.json: 缓存验证日志（自动生成）

首次使用时，请将核桃图像文件夹放在程序同目录下，然后通过界面选择根目录开始处理。
"""
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_text)
        
        print(f"✅ 文件夹结构已创建: {database_dir}")
        return True
        
    except Exception as e:
        print(f"❌ 文件夹创建失败: {e}")
        return False

if __name__ == "__main__":
    # 静默创建文件夹
    create_necessary_folders()
