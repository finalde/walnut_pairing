# 文玩核桃配对 - 相似度准确率优化指南

## 📋 目录
1. [主要调参位置](#主要调参位置)
2. [特征提取优化](#特征提取优化)
3. [相似度计算优化](#相似度计算优化)
4. [高级优化策略](#高级优化策略)

---

## 🎯 主要调参位置

### 1. GUI界面参数（`setup_ui` 方法，约780-800行）

这些参数可在界面直接调整：

```python
# Top-K 数量
self.topk_var = tk.IntVar(value=30)  # 当前默认值：30
# 建议范围：10-50
# 影响：返回的相似对数量，越大可能包含更多误匹配

# PCA维度
self.pca_var = tk.IntVar(value=256)  # 当前默认值：256
# 建议范围：128-512
# 影响：特征降维维度，影响特征保留信息量

# 相似度方法
self.similarity_var = tk.StringVar(value="cosine")  # 当前：余弦相似度
# 可选：["cosine", "euclidean", "mahalanobis"]
# 建议：cosine适合高维特征，euclidean适合标准化后的特征
```

### 2. 特征权重设置（`build_walnut_tensor` 方法，697-725行）

**当前特征维度分布：**
- 尺寸特征：3维（高度、宽度、肚围）
- 颜色特征：54维
- 轮廓特征：14维  
- 纹理特征：12288维（6角度 × 2048）

**调整建议：**

```python
# 方案1：给不同特征加权重
def build_walnut_tensor(self, walnut_features, walnut_id):
    features = walnut_features[walnut_id]
    
    # 原代码
    size_features = np.array([features['height'], features['width'], features['belly']])
    color_features = features.get('color', np.zeros(54))
    contour_features = features.get('contour', np.zeros(14))
    texture_features = features.get('fingerprint', np.zeros(6 * 2048))
    
    # 修改：添加权重（建议值）
    weight_size = 1.0      # 尺寸权重
    weight_color = 2.0     # 颜色权重（重要）
    weight_contour = 1.5   # 轮廓权重
    weight_texture = 1.0   # 纹理权重
    
    # 加权拼接
    tensor = np.concatenate([
        size_features * weight_size,
        color_features * weight_color,
        contour_features * weight_contour,
        texture_features * weight_texture
    ])
    return tensor
```

### 3. 图像预处理参数（`extract_and_resize_walnut` 方法，96-134行）

```python
# 提取和缩放尺寸
result = np.zeros((640, 640, 3), dtype=np.uint8)  # 当前：640×640
# 建议：可根据核桃大小调整，但要注意模型输入要求224×224

# 颜色阈值调整（用于核桃分割）
lower_brown = np.array([0, 30, 30])
upper_brown = np.array([30, 255, 255])
# 如果核桃颜色不在这个范围，需要调整
```

### 4. 颜色特征提取（`extract_walnut_color` 方法，515-586行）

```python
# 颜色直方图bins数量
hist_b = cv2.calcHist([img], [0], mask, [8], [0, 256])  # 当前：8 bins
# 建议：8-16，越多数值越细但计算量越大

# 颜色空间权重
# 当前使用：BGR、HSV、Lab三个颜色空间均等权重
# 可尝试：只使用对核桃最敏感的颜色空间
```

### 5. 轮廓特征提取（`extract_walnut_contour` 方法，588-646行）

```python
# 形态学操作核大小
kernel = np.ones((5,5), np.uint8)  # 当前：5×5
# 建议：3×3（更细致）到7×7（更平滑）

# Hu矩归一化方法
hu_moments = -np.sign(hu_moments) * np.log10(np.abs(hu_moments) + 1e-12)
# 当前：对数归一化，可以尝试不同的归一化方法
```

### 6. PCA降维（`process_walnuts` 方法，450-470行）

```python
# 标准化方法
scaler = StandardScaler()  # 当前：Z-score标准化
# 可尝试：
# - MinMaxScaler()  # 归一化到[0,1]
# - RobustScaler()  # 对异常值更鲁棒

# PCA求解器
pca = PCA(n_components=actual_pca_dim, svd_solver='auto')
# svd_solver选项：
# - 'auto': 自动选择
# - 'full': 完整SVD（更精确但慢）
# - 'arpack': 适合大矩阵
# - 'randomized': 适合超大矩阵，近似解
```

### 7. 相似度计算方法（`process_walnuts` 方法，476-478行）

```python
# 当前：余弦相似度
similarity = np.dot(X_final[i], X_final[j]) / (
    np.linalg.norm(X_final[i]) * np.linalg.norm(X_final[j]) + 1e-12)

# 可替换为欧氏距离相似度
# similarity = 1 / (1 + np.linalg.norm(X_final[i] - X_final[j]))

# 或曼哈顿距离相似度
# similarity = 1 / (1 + np.sum(np.abs(X_final[i] - X_final[j])))
```

### 8. 深度模型选择（`load_model` 方法，49-66行）

```python
# 当前：ResNet50
self.model = models.resnet50(weights='IMAGENET1K_V2')
# 可选模型：
# - resnet18: 更轻量，速度更快
# - resnet101: 更深度，特征更丰富
# - efficientnet_b0-b7: 效率更高
# - vision_transformer: 最新的视觉模型
```

---

## 🔧 特征提取优化

### 1. 尺寸特征校准（`extract_walnut_features` 方法，648-695行）

```python
# 像素到厘米的转换比例
pixels_per_cm = 515  # ⚠️ 这个值需要根据你的拍摄环境校准！

# 校准方法：
# 1. 拍摄一张包含已知尺寸物体（如尺子）的照片
# 2. 测量物体像素尺寸
# 3. 计算 pixels_per_cm = 像素数 / 厘米数
# 4. 更新这个值
```

### 2. 多角度特征融合策略（`process_walnuts` 方法，409-424行）

当前策略：每个角度分别提取特征后平均

```python
# 方案1：加权平均（给某些角度更高权重）
# 例如：正面(F)和顶部(T)更重要
angle_weights = {'B': 0.5, 'D': 0.5, 'F': 1.5, 'L': 1.0, 'R': 1.0, 'T': 1.5}
weighted_mean = np.average(vecs, axis=0, weights=[angle_weights[angle]]*len(vecs))

# 方案2：使用最大池化而不是平均
maxv = np.max(vecs, axis=0)

# 方案3：使用中位数（对异常值更鲁棒）
medianv = np.median(vecs, axis=0)
```

---

## 📊 相似度计算优化

### 1. 添加特征标准化（在`process_walnuts`方法中）

当前只对整体张量做标准化，可以对每个特征类型单独标准化：

```python
# 在470-478行之间添加分类特征标准化
from sklearn.preprocessing import MinMaxScaler

# 分类标准化
scaler_size = MinMaxScaler()
scaler_color = MinMaxScaler()
scaler_contour = MinMaxScaler()
scaler_texture = MinMaxScaler()

# 分别标准化后再拼接
```

### 2. 使用加权相似度

```python
# 对不同类型的特征使用不同的相似度权重
similarity_weighted = (
    0.1 * cosine_similarity(size_features[i], size_features[j]) +
    0.3 * cosine_similarity(color_features[i], color_features[j]) +
    0.2 * cosine_similarity(contour_features[i], contour_features[j]) +
    0.4 * cosine_similarity(texture_features[i], texture_features[j])
)
```

---

## 🚀 高级优化策略

### 1. 使用距离学习（Metric Learning）

训练一个专门的模型学习最优的相似度度量：

```python
# 推荐：使用Siamese Network或Triplet Network
# 需要标注一些相似/不相似的核桃对作为训练数据
```

### 2. 聚类预筛选

在处理大量核桃时，先用聚类方法分组，再在组内比较：

```python
from sklearn.cluster import KMeans

# 先用KMeans聚类
kmeans = KMeans(n_clusters=20)
cluster_labels = kmeans.fit_predict(X_final)

# 只在同一簇内的核桃之间比较相似度
for i in range(len(X_final)):
    for j in range(i+1, len(X_final)):
        if cluster_labels[i] == cluster_labels[j]:
            # 计算相似度
            similarity = ...
```

### 3. 多阶段筛选

```python
# 阶段1：用快速特征（尺寸+颜色）粗筛
# 阶段2：用完整特征（包括纹理）精确匹配
```

---

## 📝 快速优化清单

按优先级排序：

| 优先级 | 调整内容 | 预期提升 | 难度 |
|--------|---------|---------|------|
| 🔴 高 | 校准`pixels_per_cm`值 | +15-20% | ⭐ 简单 |
| 🟠 中 | 调整PCA维度(128-512) | +5-10% | ⭐ 简单 |
| 🟠 中 | 添加特征权重 | +10-15% | ⭐⭐ 中等 |
| 🟠 中 | 尝试不同相似度方法 | +5-10% | ⭐ 简单 |
| 🟡 低 | 更换深度模型 | +10-20% | ⭐⭐⭐ 复杂 |
| 🟡 低 | 优化颜色阈值 | +3-5% | ⭐⭐ 中等 |
| 🟢 可选 | 聚类预筛选 | +5-10% | ⭐⭐⭐ 复杂 |

---

## 🧪 测试建议

1. **使用已知相似对验证**：准备一些人工标注的相似/不相似核桃对
2. **交叉验证**：使用5折或10折交叉验证评估不同参数组合
3. **绘制ROC曲线**：评估不同阈值下的准确率和召回率
4. **A/B测试**：对比不同参数配置的实际效果

---

## 📚 参考资源

- PCA原理：[sklearn PCA文档](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)
- 相似度度量：[Distance Metrics详解](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise_distances.html)
- ResNet模型：[PyTorch Vision Models](https://pytorch.org/vision/stable/models.html)

---

**最后更新**：2025-10-31  
**版本**：v0.01




