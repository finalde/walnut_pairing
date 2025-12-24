# 文玩核桃配对 v0.01

基于Tkinter的核桃相似度搜索图形界面应用程序。

## 功能特点

- 🎯 **智能匹配**: 基于多维度特征（尺寸、颜色、轮廓、纹理）的核桃相似度搜索
- 🖼️ **图形界面**: 直观易用的Tkinter GUI界面
- ⚡ **实时进度**: 多阶段处理进度实时显示
- 📊 **结果展示**: 表格形式展示相似对排名
- 💾 **结果导出**: 支持JSON格式结果导出
- 🔧 **灵活配置**: 支持自定义模型路径和多种参数设置

## 系统要求

- Python 3.8+
- 支持CUDA的GPU（可选，推荐使用）

## 依赖环境

使用 conda 环境 `yolov8-gpu`，包含以下主要依赖：

```bash
torch
torchvision
opencv-python
faiss-cpu
tqdm
scikit-learn
pillow
```

## 使用方法

1. **启动应用程序**:
   
   **方式一（推荐）**: 双击桌面上的"Walnuts Pairing"快捷方式
   
   **方式二**: 运行命令行
   ```bash
   cd walnut_gui_app
   python main.py
   ```
   
   **方式三**: 运行批处理文件
   ```bash
   WalnutsPairing.bat
   ```

2. **配置参数**:
   - 选择核桃根目录（包含多个核桃子文件夹）
   - 可选：选择自定义模型文件路径
   - 设置Top-K数量、PCA维度、相似度方法等参数

3. **开始处理**:
   - 点击"开始处理"按钮
   - 实时查看处理进度和日志
   - 查看相似对结果

4. **导出结果**:
   - 点击"导出JSON"保存结果
   - 点击"查看详情"查看具体相似对信息

## 项目结构

```
walnut_pair/
├── main.py                    # 主程序入口
├── README.md                  # 项目说明
├── requirements.txt           # Python依赖列表
├── WalnutsPairing.bat         # 启动器批处理文件
├── create_folders.py          # 文件夹创建脚本
└── walnut_database/           # 自动生成的数据库目录
    ├── crop_images/           # 裁剪后的核桃图像
    ├── tensor_features_cache.pkl    # 特征缓存文件
    └── README.txt             # 数据库说明文件
```

## 核桃数据格式

核桃根目录应包含多个子文件夹，每个子文件夹代表一个核桃，包含从不同角度拍摄的图像：

```
核桃根目录/
├── walnut_001/
│   ├── walnut_001_B_1.jpg  # 底部角度
│   ├── walnut_001_D_1.jpg  # 顶部角度
│   ├── walnut_001_F_1.jpg  # 正面角度
│   ├── walnut_001_L_1.jpg  # 左侧角度
│   ├── walnut_001_R_1.jpg  # 右侧角度
│   └── walnut_001_T_1.jpg  # 顶部角度
├── walnut_002/
│   └── ...
└── ...
```

## 版本信息

- **软件名称**: 文玩核桃配对
- **版本号**: v0.01
- **开发环境**: conda yolov8-gpu

## 注意事项

- 首次运行会创建数据库目录和缓存文件
- 支持GPU加速处理（如果可用）
- 处理大量核桃时可能需要较长时间
- 建议使用特征缓存功能提高重复处理效率
