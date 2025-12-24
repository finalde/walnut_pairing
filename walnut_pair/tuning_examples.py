#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调参示例代码
提供几种常见的优化方案供参考
"""

import numpy as np
import cv2
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans


# ==================== 方案1：特征加权 ====================
def build_weighted_tensor(walnut_features, walnut_id):
    """方案1：为不同特征类型添加权重"""
    features = walnut_features[walnut_id]
    
    size_features = np.array([features['height'], features['width'], features['belly']])
    color_features = features.get('color', np.zeros(54))
    contour_features = features.get('contour', np.zeros(14))
    texture_features = features.get('fingerprint', np.zeros(6 * 2048))
    
    # 🔧 可调参数：权重比例（根据实际效果调整）
    weights = {
        'size': 1.0,      # 尺寸权重
        'color': 2.0,     # 颜色权重（重要）
        'contour': 1.5,   # 轮廓权重
        'texture': 1.0    # 纹理权重
    }
    
    tensor = np.concatenate([
        size_features * weights['size'],
        color_features * weights['color'],
        contour_features * weights['contour'],
        texture_features * weights['texture']
    ])
    return tensor


# ==================== 方案2：改进的PCA降维 ====================
def improved_pca_reduction(X, pca_dim=256, scaler_type='standard'):
    """方案2：改进的PCA降维"""
    
    # 🔧 可调参数：标准化方法
    scalers = {
        'standard': StandardScaler(),   # Z-score（当前使用）
        'minmax': MinMaxScaler(),       # 归一化到[0,1]
        'robust': RobustScaler()        # 对异常值鲁棒
    }
    
    scaler = scalers.get(scaler_type, StandardScaler())
    X_scaled = scaler.fit_transform(X)
    
    # 🔧 可调参数：PCA求解器
    pca = PCA(n_components=pca_dim, svd_solver='auto')
    # svd_solver选项：
    # - 'auto': 自动选择（当前使用）
    # - 'full': 完整SVD（最精确）
    # - 'arpack': 适合大矩阵
    # - 'randomized': 近似解，适合超大矩阵
    
    X_final = pca.fit_transform(X_scaled)
    
    print(f"保留的方差比例: {pca.explained_variance_ratio_.sum():.2%}")
    print(f"前10个主成分解释的方差: {pca.explained_variance_ratio_[:10].sum():.2%}")
    
    return X_final, pca


# ==================== 方案3：多相似度度量融合 ====================
def calculate_multi_similarity(vec1, vec2):
    """方案3：融合多种相似度度量"""
    
    # 余弦相似度
    cosine_sim = np.dot(vec1, vec2) / (
        np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-12)
    
    # 欧氏距离相似度
    euclidean_dist = np.linalg.norm(vec1 - vec2)
    euclidean_sim = 1 / (1 + euclidean_dist)
    
    # 曼哈顿距离相似度
    manhattan_dist = np.sum(np.abs(vec1 - vec2))
    manhattan_sim = 1 / (1 + manhattan_dist)
    
    # 🔧 可调参数：融合权重
    weights = {
        'cosine': 0.5,
        'euclidean': 0.3,
        'manhattan': 0.2
    }
    
    final_similarity = (
        weights['cosine'] * cosine_sim +
        weights['euclidean'] * euclidean_sim +
        weights['manhattan'] * manhattan_sim
    )
    
    return final_similarity


# ==================== 方案4：聚类预筛选 ====================
def similarity_with_clustering(X_final, n_clusters=20):
    """方案4：使用聚类预筛选，减少计算量"""
    
    # 🔧 可调参数：聚类数量
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_final)
    
    # 只在同一簇内的样本之间计算相似度
    pairs = []
    for i in range(len(X_final)):
        for j in range(i+1, len(X_final)):
            if cluster_labels[i] == cluster_labels[j]:
                similarity = np.dot(X_final[i], X_final[j]) / (
                    np.linalg.norm(X_final[i]) * np.linalg.norm(X_final[j]) + 1e-12)
                pairs.append((i, j, similarity))
    
    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs


# ==================== 方案5：自适应角度加权 ====================
def adaptive_angle_weighting(angle_features_dict):
    """方案5：根据角度特征质量自适应加权"""
    
    angles = ['B', 'D', 'F', 'L', 'R', 'T']
    angle_names = ['背面', '底部', '正面', '左侧', '右侧', '顶部']
    
    # 计算每个角度特征的"质量"（方差越大，信息量越大）
    angle_qualities = {}
    for angle in angles:
        if angle_features_dict[angle] is not None:
            # 使用特征的标准差作为质量指标
            quality = np.std(angle_features_dict[angle])
            angle_qualities[angle] = quality
        else:
            angle_qualities[angle] = 0
    
    # 归一化质量分数
    total_quality = sum(angle_qualities.values())
    if total_quality > 0:
        angle_weights = {k: v/total_quality for k, v in angle_qualities.items()}
    else:
        angle_weights = {angle: 1/6 for angle in angles}
    
    print("角度权重：")
    for angle, name in zip(angles, angle_names):
        print(f"  {name}({angle}): {angle_weights[angle]:.3f}")
    
    return angle_weights


# ==================== 方案6：颜色特征改进 ====================
def extract_improved_color_features(img, mask):
    """方案6：改进的颜色特征提取"""
    
    # 🔧 可调参数：直方图bins数量
    hist_bins = 16  # 原值：8，增加细节但计算量增大
    
    # 增强颜色空间
    bgr_mean = np.mean(img[mask > 0], axis=0)
    hsv_mean = np.mean(cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[mask > 0], axis=0)
    lab_mean = np.mean(cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[mask > 0], axis=0)
    
    # 增加Gabor纹理特征
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gabor_kernels = []
    for theta in [0, 45, 90, 135]:
        kernel = cv2.getGaborKernel((21, 21), 5, theta, 10, 0.5, 0, ktype=cv2.CV_32F)
        gabor_kernels.append(kernel)
    
    gabor_features = []
    for kernel in gabor_kernels:
        filtered = cv2.filter2D(gray, cv2.CV_8UC3, kernel)
        gabor_features.append(np.mean(filtered[mask > 0]))
        gabor_features.append(np.std(filtered[mask > 0]))
    
    # 组合所有颜色特征
    color_features = np.concatenate([
        bgr_mean / 255.0,
        hsv_mean,
        lab_mean,
        np.array(gabor_features) / 255.0
    ])
    
    return color_features


# ==================== 方案7：两阶段匹配 ====================
def two_stage_matching(X_final, topk=30, stage1_k=100):
    """方案7：两阶段匹配策略"""
    
    # 阶段1：快速粗筛（使用部分特征）
    # 假设前500维是快速特征（尺寸+颜色+轮廓）
    X_fast = X_final[:, :min(500, X_final.shape[1])]
    
    fast_pairs = []
    for i in range(len(X_fast)):
        for j in range(i+1, len(X_fast)):
            similarity = np.dot(X_fast[i], X_fast[j]) / (
                np.linalg.norm(X_fast[i]) * np.linalg.norm(X_fast[j]) + 1e-12)
            fast_pairs.append((i, j, similarity))
    
    fast_pairs.sort(key=lambda x: x[2], reverse=True)
    candidate_indices = set()
    for i, j, _ in fast_pairs[:stage1_k]:
        candidate_indices.add(i)
        candidate_indices.add(j)
    
    # 阶段2：精确匹配（使用完整特征）
    final_pairs = []
    candidate_list = list(candidate_indices)
    for i_idx, i in enumerate(candidate_list):
        for j_idx, j in enumerate(candidate_list):
            if j_idx > i_idx:
                similarity = np.dot(X_final[i], X_final[j]) / (
                    np.linalg.norm(X_final[i]) * np.linalg.norm(X_final[j]) + 1e-12)
                final_pairs.append((i, j, similarity))
    
    final_pairs.sort(key=lambda x: x[2], reverse=True)
    return final_pairs[:topk]


# ==================== 使用示例 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("文玩核桃配对 - 调参示例代码")
    print("=" * 60)
    
    # 示例1：测试不同的PCA维度对特征保留的影响
    print("\n【示例1】PCA维度分析")
    print("-" * 60)
    np.random.seed(42)
    X = np.random.randn(100, 12359)  # 模拟特征矩阵
    
    for pca_dim in [64, 128, 256, 512]:
        _, pca = improved_pca_reduction(X, pca_dim=pca_dim)
        print(f"PCA维度={pca_dim}: "
              f"保留方差={pca.explained_variance_ratio_.sum():.2%}")
    
    # 示例2：测试聚类数量对筛选效果的影响
    print("\n【示例2】聚类预筛选分析")
    print("-" * 60)
    np.random.seed(42)
    X_final = improved_pca_reduction(X, pca_dim=256)[0]
    
    for n_clusters in [10, 20, 30, 50]:
        pairs = similarity_with_clustering(X_final, n_clusters=n_clusters)
        print(f"聚类数量={n_clusters}: 候选对数量={len(pairs)}")
    
    # 示例3：测试自适应角度加权
    print("\n【示例3】自适应角度加权")
    print("-" * 60)
    angle_features = {
        'B': np.random.randn(2048),
        'D': np.random.randn(2048) * 2,  # 方差更大的角度
        'F': np.random.randn(2048) * 0.5,
        'L': np.random.randn(2048),
        'R': np.random.randn(2048),
        'T': np.random.randn(2048) * 1.5
    }
    weights = adaptive_angle_weighting(angle_features)
    
    print("\n完成！")
    print("=" * 60)
    print("提示：这些示例代码可以直接集成到main.py中使用")
    print("建议按照PARAMETER_TUNING_GUIDE.md的优先级顺序逐一尝试优化")

