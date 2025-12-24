#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文玩核桃配对 v0.01
基于Tkinter的核桃相似度搜索图形界面
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import json
import pickle
import cv2
import numpy as np
from PIL import Image, ImageTk
import torch
import torchvision.models as models
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm
import tempfile
import shutil
from glob import glob
import hashlib
import time
from datetime import datetime
from pathlib import Path

# Ensure console uses UTF-8 to avoid encoding errors on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

class WalnutProcessor:
    """核桃处理核心类"""
    
    def __init__(self):
        self.device = torch.device('cpu')  # 强制使用CPU推理
        self.model = None
        self.is_running = False
        self.progress_queue = queue.Queue()
        
    def load_model(self, model_path=None):
        """加载模型"""
        try:
            if model_path and os.path.exists(model_path):
                # 加载自定义模型
                self.model = torch.load(model_path, map_location=self.device)
                self.model.eval()
                self.progress_queue.put(("log", f"✅ 自定义模型加载成功: {model_path}"))
            else:
                # 加载预训练模型
                self.model = models.resnet50(weights='IMAGENET1K_V2')
                self.model.fc = torch.nn.Identity()
                self.model.to(self.device).eval()
                self.progress_queue.put(("log", "✅ ResNet50预训练模型加载成功"))
            return True
        except Exception as e:
            self.progress_queue.put(("error", f"❌ 模型加载失败: {e}"))
            return False
    
    def extract_walnut_size(self, img_path):
        """从原图中提取核桃轮廓并计算尺寸"""
        try:
            img = cv2.imread(img_path)
            if img is None:
                return False, (0, 0)
            
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_brown = np.array([0, 30, 30])
            upper_brown = np.array([30, 255, 255])
            mask = cv2.inRange(hsv, lower_brown, upper_brown)
            
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return False, (0, 0)
            
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            return True, (w, h)
            
        except Exception as e:
            self.progress_queue.put(("log", f"Error processing image {img_path}: {e}"))
            return False, (0, 0)
    
    def extract_and_resize_walnut(self, img_path, output_path):
        """提取核桃并缩放到640×640黑色背景"""
        try:
            img = cv2.imread(img_path)
            if img is None:
                return False
            
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_brown = np.array([0, 30, 30])
            upper_brown = np.array([30, 255, 255])
            mask = cv2.inRange(hsv, lower_brown, upper_brown)
            
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return False
            
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            walnut_region = img[y:y+h, x:x+w]
            
            result = np.zeros((640, 640, 3), dtype=np.uint8)
            scale = min(640.0 / w, 640.0 / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            offset_x = (640 - new_w) // 2
            offset_y = (640 - new_h) // 2
            
            walnut_resized = cv2.resize(walnut_region, (new_w, new_h))
            result[offset_y:offset_y+new_h, offset_x:offset_x+new_w] = walnut_resized
            cv2.imwrite(output_path, result)
            return True
            
        except Exception as e:
            self.progress_queue.put(("log", f"Error processing image {img_path}: {e}"))
            return False
    
    def img2vec(self, path):
        """单张图像 → 2048维向量"""
        try:
            img = cv2.imread(path)
            if img is None:
                return None
            img = img[:, :, ::-1]  # BGR→RGB
            img = cv2.resize(img, (224, 224))
            img = img.astype(np.float32) / 255.0
            
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            img = (img - mean) / std
            
            tensor = torch.from_numpy(img.astype(np.float32)).permute(2, 0, 1).unsqueeze(0).to(self.device)
            with torch.no_grad():
                vec = self.model(tensor).squeeze().cpu().numpy()
            
            if np.any(np.isnan(vec)) or np.any(np.isinf(vec)) or np.all(vec == 0):
                return None
                
            vec_norm = vec / (np.linalg.norm(vec) + 1e-12)
            return vec_norm
        except Exception as e:
            self.progress_queue.put(("log", f"Error processing image {path}: {e}"))
            return None
    
    def validate_cache_integrity(self, root_dir, database_dir, cache_file):
        """智能缓存验证系统"""
        try:
            self.progress_queue.put(("log", "🔍 开始智能缓存验证..."))
            
            # 检查缓存文件是否存在
            if not os.path.exists(cache_file):
                self.progress_queue.put(("log", "❌ 缓存文件不存在"))
                return False
            
            # 检查缓存文件大小
            cache_size = os.path.getsize(cache_file)
            if cache_size < 100:  # 小于100字节认为是无效缓存
                self.progress_queue.put(("log", f"❌ 缓存文件过小 ({cache_size} 字节)"))
                return False
            
            # 检查缓存文件内容
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # 验证缓存数据结构
                required_keys = ['all_tensors', 'id2folder', 'walnut_sizes', 'walnut_features']
                for key in required_keys:
                    if key not in cache_data:
                        self.progress_queue.put(("log", f"❌ 缓存缺少必要字段: {key}"))
                        return False
                
                # 验证数据完整性
                if len(cache_data['all_tensors']) == 0:
                    self.progress_queue.put(("log", "❌ 缓存特征张量为空"))
                    return False
                
                if len(cache_data['id2folder']) == 0:
                    self.progress_queue.put(("log", "❌ 缓存ID映射为空"))
                    return False
                
                # 验证源数据一致性
                walnut_folders = [f for f in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, f))]
                cached_walnuts = set(cache_data['id2folder'].values())
                current_walnuts = set(walnut_folders)
                
                if cached_walnuts != current_walnuts:
                    self.progress_queue.put(("log", f"❌ 源数据不一致: 缓存{len(cached_walnuts)}个, 当前{len(current_walnuts)}个"))
                    return False
                
                # 验证裁剪图像完整性
                crop_dir = os.path.join(database_dir, 'crop_images')
                for walnut_id in cached_walnuts:
                    walnut_crop_dir = os.path.join(crop_dir, walnut_id)
                    if not os.path.exists(walnut_crop_dir):
                        self.progress_queue.put(("log", f"❌ 裁剪图像目录不存在: {walnut_id}"))
                        return False
                    
                    # 检查每个核桃的六个角度图像
                    angle_images = {}
                    for angle in ['B', 'D', 'F', 'L', 'R', 'T']:
                        angle_files = [f for f in os.listdir(walnut_crop_dir) if f.endswith(('.jpg', '.png', '.jpeg')) and f'_{angle}_' in f]
                        if not angle_files:
                            self.progress_queue.put(("log", f"❌ 核桃 {walnut_id} 缺少角度 {angle} 的图像"))
                            return False
                
                self.progress_queue.put(("log", f"✅ 缓存验证通过: {len(cached_walnuts)} 个核桃, {len(cache_data['all_tensors'])} 个特征张量"))
                return True
                
            except Exception as e:
                self.progress_queue.put(("log", f"❌ 缓存文件解析失败: {e}"))
                return False
                
        except Exception as e:
            self.progress_queue.put(("log", f"❌ 缓存验证过程出错: {e}"))
            return False
    
    def create_cache_log(self, root_dir, database_dir, cache_file):
        """创建缓存日志记录"""
        try:
            log_file = os.path.join(database_dir, 'cache_validation_log.json')
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'root_dir': root_dir,
                'database_dir': database_dir,
                'cache_file': cache_file,
                'cache_size': os.path.getsize(cache_file) if os.path.exists(cache_file) else 0,
                'walnut_count': len([f for f in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, f))]),
                'validation_result': 'PASS' if self.validate_cache_integrity(root_dir, database_dir, cache_file) else 'FAIL'
            }
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            
            self.progress_queue.put(("log", f"📝 缓存验证日志已保存: {log_file}"))
            
        except Exception as e:
            self.progress_queue.put(("log", f"❌ 缓存日志创建失败: {e}"))
    
    def process_walnuts(self, root_dir, topk=30, pca_dim=256, similarity_method='cosine', 
                       use_cache=False, force_reprocess=False, model_path=None):
        """主处理流程"""
        try:
            self.is_running = True
            
            # 加载模型
            self.progress_queue.put(("progress", 10, "加载模型中..."))
            if not self.load_model(model_path):
                return
            
            # 创建数据库目录
            database_dir = os.path.join(os.path.dirname(__file__), 'walnut_database')
            os.makedirs(database_dir, exist_ok=True)
            crop_dir = os.path.join(database_dir, 'crop_images')
            os.makedirs(crop_dir, exist_ok=True)
            cache_file = os.path.join(database_dir, 'tensor_features_cache.pkl')
            
            self.progress_queue.put(("log", f"数据库目录: {database_dir}"))
            self.progress_queue.put(("log", f"裁剪图像目录: {crop_dir}"))
            
            # 创建缓存验证日志
            self.create_cache_log(root_dir, database_dir, cache_file)
            
            # 初始化变量
            all_tensors, id2folder, walnut_sizes, walnut_features = [], {}, {}, {}
            
            # 智能缓存验证
            cache_valid = False
            if use_cache and os.path.exists(cache_file) and not force_reprocess:
                cache_valid = self.validate_cache_integrity(root_dir, database_dir, cache_file)
                if cache_valid:
                    self.progress_queue.put(("log", "🔍 从缓存加载特征数据..."))
                    try:
                        with open(cache_file, 'rb') as f:
                            cache_data = pickle.load(f)
                        all_tensors = cache_data['all_tensors']
                        id2folder = cache_data['id2folder']
                        walnut_sizes = cache_data['walnut_sizes']
                        walnut_features = cache_data['walnut_features']
                        self.progress_queue.put(("log", f"✅ 从缓存加载 {len(all_tensors)} 个核桃的特征数据"))
                    except Exception as e:
                        self.progress_queue.put(("log", f"❌ 缓存加载失败: {e}"))
                        cache_valid = False
                else:
                    self.progress_queue.put(("log", "❌ 缓存验证失败，将重新处理数据"))
            
            if not use_cache or force_reprocess or not all_tensors:
                self.progress_queue.put(("progress", 30, "处理核桃图像中..."))
                all_tensors, id2folder, walnut_sizes, walnut_features = [], {}, {}, {}
                
                walnut_folders = [f for f in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, f))]
                
                for idx, folder in enumerate(tqdm(walnut_folders, desc='处理核桃')):
                    if not self.is_running:
                        break
                        
                    folder_path = os.path.join(root_dir, folder)
                    self.progress_queue.put(("log", f"处理核桃: {folder}"))
                    
                    # 创建裁剪子文件夹
                    crop_subdir = os.path.join(crop_dir, folder)
                    os.makedirs(crop_subdir, exist_ok=True)
                    
                    # 阶段1：从原图中提取尺寸信息
                    angle_sizes = {'B': [], 'D': [], 'F': [], 'L': [], 'R': [], 'T': []}
                    
                    # 阶段2：提取并缩放核桃图像
                    views = {'B': [], 'D': [], 'F': [], 'L': [], 'R': [], 'T': []}
                    
                    for fn in os.listdir(folder_path):
                        if not fn.lower().endswith(('.jpg', '.png', '.jpeg')):
                            continue
                            
                        # 分类角度
                        angle = None
                        if '_B_' in fn:
                            angle = 'B'
                        elif '_D_' in fn:
                            angle = 'D'
                        elif '_F_' in fn:
                            angle = 'F'
                        elif '_L_' in fn:
                            angle = 'L'
                        elif '_R_' in fn:
                            angle = 'R'
                        elif '_T_' in fn:
                            angle = 'T'
                        
                        if angle:
                            input_path = os.path.join(folder_path, fn)
                            output_path = os.path.join(crop_subdir, fn)
                            
                            # 阶段1：提取原始尺寸
                            success, size = self.extract_walnut_size(input_path)
                            if success:
                                angle_sizes[angle].append(size)
                            
                            # 阶段2：提取并缩放核桃图像
                            success = self.extract_and_resize_walnut(input_path, output_path)
                            if success:
                                views[angle].append(output_path)
                    
                    # 计算每个角度的平均尺寸
                    avg_sizes = {}
                    for angle in ['B', 'D', 'F', 'L', 'R', 'T']:
                        if angle_sizes[angle]:
                            sizes_array = np.array(angle_sizes[angle])
                            avg_width = np.mean(sizes_array[:, 0])
                            avg_height = np.mean(sizes_array[:, 1])
                            avg_sizes[angle] = (avg_width, avg_height)
                        else:
                            avg_sizes[angle] = (0, 0)
                    
                    walnut_sizes[idx] = avg_sizes
                    
                    # 阶段3：提取多维度特征
                    walnut_features[idx] = {}
                    
                    # 提取尺寸特征
                    size_features = self.extract_walnut_features({idx: avg_sizes})
                    walnut_features[idx].update(size_features[idx])
                    
                    # 提取颜色特征（从每个角度选择一张代表性图像）
                    color_features_list = []
                    for angle in ['B', 'D', 'F', 'L', 'R', 'T']:
                        if views[angle]:
                            color_feature = self.extract_walnut_color(views[angle][0])
                            if color_feature is not None:
                                color_features_list.append(color_feature)
                    
                    if color_features_list:
                        walnut_features[idx]['color'] = np.mean(color_features_list, axis=0)
                    else:
                        # 标准化颜色特征维度为54
                        walnut_features[idx]['color'] = np.zeros(54)
                    
                    # 提取轮廓特征（从每个角度选择一张代表性图像）
                    contour_features_list = []
                    for angle in ['B', 'D', 'F', 'L', 'R', 'T']:
                        if views[angle]:
                            contour_feature = self.extract_walnut_contour(views[angle][0])
                            if contour_feature is not None:
                                contour_features_list.append(contour_feature)
                    
                    if contour_features_list:
                        walnut_features[idx]['contour'] = np.mean(contour_features_list, axis=0)
                    else:
                        walnut_features[idx]['contour'] = np.zeros(14)
                    
                    # 提取纹理特征（指纹）
                    fp = []
                    for angle in ['B', 'D', 'F', 'L', 'R', 'T']:
                        vecs = []
                        for img_path in views[angle]:
                            vec = self.img2vec(img_path)
                            if vec is not None:
                                vecs.append(vec)
                        
                        if len(vecs) == 0:
                            fp.append(np.zeros(2048))
                        else:
                            meanv = np.stack(vecs).mean(0)
                            meanv = meanv / (np.linalg.norm(meanv) + 1e-12)
                            fp.append(meanv)
                    
                    fingerprint = np.hstack(fp)
                    walnut_features[idx]['fingerprint'] = fingerprint
                    
                    # 构建特征张量
                    tensor = self.build_walnut_tensor(walnut_features, idx)
                    all_tensors.append(tensor)
                    id2folder[idx] = folder
            
            # 保存到缓存
            if use_cache:
                try:
                    cache_data = {
                        'all_tensors': all_tensors,
                        'id2folder': id2folder,
                        'walnut_sizes': walnut_sizes,
                        'walnut_features': walnut_features
                    }
                    with open(cache_file, 'wb') as f:
                        pickle.dump(cache_data, f)
                    self.progress_queue.put(("log", f"✅ 特征数据已保存到缓存: {cache_file}"))
                except Exception as e:
                    self.progress_queue.put(("log", f"❌ 缓存保存失败: {e}"))
            
            if not self.is_running:
                return
            
            # 计算相似度
            self.progress_queue.put(("progress", 80, "计算相似度中..."))
            X = np.vstack(all_tensors).astype(np.float32)
            
            # 标准化和PCA
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # 动态调整PCA维度，确保不超过样本数量
            n_samples, n_features = X_scaled.shape
            actual_pca_dim = min(pca_dim, n_samples - 1, n_features)
            if actual_pca_dim < 2:
                actual_pca_dim = min(2, n_samples - 1)
            
            self.progress_queue.put(("log", f"实际PCA维度: {actual_pca_dim} (样本数: {n_samples})"))
            
            if actual_pca_dim > 0:
                pca = PCA(n_components=actual_pca_dim, svd_solver='auto')
                X_final = pca.fit_transform(X_scaled).astype(np.float32)
            else:
                X_final = X_scaled.astype(np.float32)
            
            # 计算相似对
            pairs = []
            for i in range(len(X_final)):
                for j in range(i+1, len(X_final)):
                    similarity = np.dot(X_final[i], X_final[j]) / (
                        np.linalg.norm(X_final[i]) * np.linalg.norm(X_final[j]) + 1e-12)
                    pairs.append((i, j, similarity))
            
            pairs.sort(key=lambda x: x[2], reverse=True)
            
            # 选择Top-K对
            final_pairs = []
            used_walnuts = set()
            for i, j, similarity in pairs:
                if len(final_pairs) >= topk:
                    break
                if i not in used_walnuts and j not in used_walnuts:
                    final_pairs.append((i, j, similarity))
                    used_walnuts.add(i)
                    used_walnuts.add(j)
            
            # 保存结果
            self.progress_queue.put(("progress", 95, "保存结果中..."))
            results = {}
            for a, b, similarity in final_pairs:
                pair_key = f"{id2folder[a]}--{id2folder[b]}"
                results[pair_key] = {
                    "tensor_similarity": float(round(similarity, 4)),
                    "similarity_method": similarity_method,
                    "walnut_a": id2folder[a],
                    "walnut_b": id2folder[b]
                }
            
            # 发送结果
            self.progress_queue.put(("results", results))
            self.progress_queue.put(("progress", 100, "处理完成!"))
            self.progress_queue.put(("log", f"✅ 处理完成! 找到 {len(final_pairs)} 对相似核桃"))
            
        except Exception as e:
            self.progress_queue.put(("error", f"处理过程中出错: {e}"))
        finally:
            self.is_running = False
    
    def extract_walnut_color(self, img_path):
        """提取核桃的全面颜色特征"""
        try:
            img = cv2.imread(img_path)
            if img is None:
                return None
            
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            
            lower_brown = np.array([0, 30, 30])
            upper_brown = np.array([30, 255, 255])
            mask = cv2.inRange(hsv, lower_brown, upper_brown)
            walnut_region = cv2.bitwise_and(img, img, mask=mask)
            
            non_zero_coords = np.where(mask > 0)
            if len(non_zero_coords[0]) == 0:
                return None
            
            bgr_pixels = img[non_zero_coords]
            hsv_pixels = hsv[non_zero_coords]
            lab_pixels = lab[non_zero_coords]
            
            # RGB特征
            bgr_mean = np.mean(bgr_pixels, axis=0) / 255.0
            bgr_std = np.std(bgr_pixels, axis=0) / 255.0
            
            # HSV特征
            hsv_mean = np.mean(hsv_pixels, axis=0)
            hsv_mean[0] = hsv_mean[0] / 180.0
            hsv_mean[1:] = hsv_mean[1:] / 255.0
            hsv_std = np.std(hsv_pixels, axis=0)
            hsv_std[0] = hsv_std[0] / 180.0
            hsv_std[1:] = hsv_std[1:] / 255.0
            
            # Lab特征
            lab_mean = np.mean(lab_pixels, axis=0)
            lab_mean[0] = lab_mean[0] / 255.0
            lab_mean[1:] = (lab_mean[1:] + 128) / 255.0
            lab_std = np.std(lab_pixels, axis=0)
            lab_std[0] = lab_std[0] / 255.0
            lab_std[1:] = lab_std[1:] / 255.0
            
            # 颜色直方图
            hist_b = cv2.calcHist([img], [0], mask, [8], [0, 256]).flatten()
            hist_g = cv2.calcHist([img], [1], mask, [8], [0, 256]).flatten()
            hist_r = cv2.calcHist([img], [2], mask, [8], [0, 256]).flatten()
            hist_bgr = np.concatenate([hist_b, hist_g, hist_r]) / np.sum(hist_b + hist_g + hist_r + 1e-12)
            
            # 颜色矩
            color_moments = []
            for channel in range(3):
                channel_pixels = bgr_pixels[:, channel]
                mean = np.mean(channel_pixels)
                std = np.std(channel_pixels)
                skewness = np.mean((channel_pixels - mean) ** 3) / (std ** 3 + 1e-12)
                color_moments.extend([mean / 255.0, std / 255.0, skewness])
            
            # 主色调
            dominant_colors = bgr_mean
            
            # 构建综合颜色特征向量
            color_features = np.concatenate([
                bgr_mean, bgr_std, hsv_mean, hsv_std, lab_mean, lab_std,
                hist_bgr, color_moments, dominant_colors
            ])
            
            return color_features
            
        except Exception as e:
            self.progress_queue.put(("log", f"Error extracting color from {img_path}: {e}"))
            return None

    def extract_walnut_contour(self, img_path):
        """提取核桃精确轮廓特征"""
        try:
            img = cv2.imread(img_path)
            if img is None:
                return None
            
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_brown = np.array([0, 30, 30])
            upper_brown = np.array([30, 255, 255])
            mask = cv2.inRange(hsv, lower_brown, upper_brown)
            
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None
            
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            perimeter = cv2.arcLength(largest_contour, True)
            
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
            else:
                circularity = 0
            
            hull = cv2.convexHull(largest_contour)
            hull_area = cv2.contourArea(hull)
            convexity = area / hull_area if hull_area > 0 else 0
            
            hull_defects = cv2.convexityDefects(largest_contour, cv2.convexHull(largest_contour, returnPoints=False))
            if hull_defects is not None:
                defect_depth_sum = sum(defect[0, 3] for defect in hull_defects) / 256.0
                avg_defect_depth = defect_depth_sum / len(hull_defects)
            else:
                avg_defect_depth = 0
            
            moments = cv2.moments(largest_contour)
            hu_moments = cv2.HuMoments(moments)
            hu_moments = -np.sign(hu_moments) * np.log10(np.abs(hu_moments) + 1e-12)
            
            complexity = (perimeter * perimeter) / area if area > 0 else 0
            x, y, w, h = cv2.boundingRect(largest_contour)
            aspect_ratio = w / h if h > 0 else 0
            
            contour_features = np.array([
                np.log(area + 1), np.log(perimeter + 1), circularity, convexity,
                avg_defect_depth, np.log(complexity + 1), aspect_ratio
            ])
            
            contour_features = np.concatenate([contour_features, hu_moments.flatten()])
            return contour_features
            
        except Exception as e:
            self.progress_queue.put(("log", f"Error extracting contour from {img_path}: {e}"))
            return None

    def extract_walnut_features(self, walnut_sizes):
        """从六个角度的尺寸数据中提取核桃的三个主要特征值"""
        features = {}
        pixels_per_cm = 515
        
        for walnut_id, sizes in walnut_sizes.items():
            height_values = []
            width_values = []
            belly_values = []
            
            for angle, (w, h) in sizes.items():
                if w == 0 or h == 0:
                    continue
                    
                if angle in ['F', 'B', 'L', 'R']:
                    height_values.append(h)
                
                if angle == 'F' or angle == 'B':
                    width_values.append(w)
                elif angle == 'T':
                    width_values.append(w)
                elif angle == 'D':
                    width_values.append(w)
                
                if angle == 'L' or angle == 'R':
                    belly_values.append(w)
                elif angle == 'T':
                    belly_values.append(h)
                    belly_values.append(w)
                elif angle == 'D':
                    belly_values.append(h)
                    belly_values.append(w)
            
            height = np.mean(height_values) if height_values else 0
            width = np.mean(width_values) if width_values else 0
            belly = np.mean(belly_values) if belly_values else 0
            
            height_cm = height / pixels_per_cm if height > 0 else 0
            width_cm = width / pixels_per_cm if width > 0 else 0
            belly_cm = belly / pixels_per_cm if belly > 0 else 0
            
            features[walnut_id] = {
                'height': float(round(height_cm, 4)),
                'width': float(round(width_cm, 4)),
                'belly': float(round(belly_cm, 4))
            }
        
        return features

    def build_walnut_tensor(self, walnut_features, walnut_id):
        """构建核桃的统一特征张量"""
        features = walnut_features[walnut_id]
        
        # 尺寸特征 (3维)
        size_features = np.array([
            features['height'],
            features['width'], 
            features['belly']
        ])
        
        # 颜色特征 (54维)
        color_features = features.get('color', np.zeros(54))
        
        # 轮廓特征 (14维)
        contour_features = features.get('contour', np.zeros(14))
        
        # 纹理特征 (6*2048=12288维)
        texture_features = features.get('fingerprint', np.zeros(6 * 2048))
        
        # 拼接成统一张量
        tensor = np.concatenate([
            size_features,
            color_features,
            contour_features,
            texture_features
        ])
        
        return tensor

    def stop_processing(self):
        """停止处理"""
        self.is_running = False


class WalnutGUI:
    """核桃相似度搜索GUI界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("文玩核桃配对 v0.01")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        self.processor = WalnutProcessor()
        self.setup_ui()
        
        # 启动进度更新线程
        self.update_progress()
    
    def setup_ui(self):
        """设置用户界面 - 使用可调节的自适应布局"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="文玩核桃配对 v0.01", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 创建水平分割的主容器
        main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_paned, text="控制面板", padding="10")
        main_paned.add(control_frame, weight=1)
        
        # 核桃目录选择
        ttk.Label(control_frame, text="核桃根目录:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.root_dir_var = tk.StringVar()
        root_dir_entry = ttk.Entry(control_frame, textvariable=self.root_dir_var, width=30)
        root_dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Button(control_frame, text="浏览", 
                  command=self.browse_root_dir).grid(row=0, column=2, padx=(5, 0))
        
        # 模型路径选择
        ttk.Label(control_frame, text="模型路径(可选):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.model_path_var = tk.StringVar()
        model_path_entry = ttk.Entry(control_frame, textvariable=self.model_path_var, width=30)
        model_path_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Button(control_frame, text="浏览", 
                  command=self.browse_model_path).grid(row=1, column=2, padx=(5, 0))
        
        # 参数设置
        params_frame = ttk.Frame(control_frame)
        params_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(params_frame, text="Top-K 数量:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.topk_var = tk.IntVar(value=30)
        ttk.Spinbox(params_frame, from_=1, to=100, textvariable=self.topk_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        ttk.Label(params_frame, text="PCA维度:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.pca_var = tk.IntVar(value=256)
        ttk.Spinbox(params_frame, from_=32, to=512, textvariable=self.pca_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        ttk.Label(params_frame, text="相似度方法:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.similarity_var = tk.StringVar(value="cosine")
        similarity_combo = ttk.Combobox(params_frame, textvariable=self.similarity_var, 
                                       values=["cosine", "euclidean", "mahalanobis"], width=10)
        similarity_combo.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # 选项
        self.cache_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame, text="启用特征缓存", variable=self.cache_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.force_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(params_frame, text="强制重新处理", variable=self.force_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # 控制按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.start_button = ttk.Button(button_frame, text="开始处理", command=self.start_processing)
        self.start_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 5))
        
        ttk.Button(button_frame, text="清空日志", command=self.clear_log).grid(row=0, column=2)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_label = ttk.Label(control_frame, text="就绪")
        self.progress_label.grid(row=5, column=0, columnspan=3, sticky=tk.W)
        
        # 处理日志区域 - 移动到控制面板下方
        log_frame = ttk.LabelFrame(control_frame, text="处理日志", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置控制面板网格权重
        control_frame.columnconfigure(1, weight=1)
        control_frame.rowconfigure(6, weight=1)  # 让日志区域可以扩展
        
        # 右侧结果区域
        result_container = ttk.Frame(main_paned)
        main_paned.add(result_container, weight=3)
        
        # 创建垂直分割的结果区域
        result_paned = ttk.PanedWindow(result_container, orient=tk.VERTICAL)
        result_paned.pack(fill=tk.BOTH, expand=True)
        
        # 上半部分：结果标签页
        result_tab_frame = ttk.Frame(result_paned)
        result_paned.add(result_tab_frame, weight=1)
        
        # 使用Notebook实现标签页
        self.result_notebook = ttk.Notebook(result_tab_frame)
        self.result_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 标签页1：相似对分析
        result_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(result_tab, text="相似对分析")
        
        # 在相似对分析标签页中使用垂直分割
        result_tab_paned = ttk.PanedWindow(result_tab, orient=tk.VERTICAL)
        result_tab_paned.pack(fill=tk.BOTH, expand=True)
        
        # 上半部分：结果列表
        result_list_frame = ttk.LabelFrame(result_tab_paned, text="相似对列表", padding="10")
        result_tab_paned.add(result_list_frame, weight=1)
        
        # 结果表格
        columns = ("排名", "核桃A", "核桃B", "相似度")
        self.result_tree = ttk.Treeview(result_list_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=80)
        
        self.result_tree.column("核桃A", width=120)
        self.result_tree.column("核桃B", width=120)
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(result_list_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.result_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        tree_scroll.pack(fill=tk.Y, side=tk.RIGHT)
        
        # 结果操作按钮
        result_buttons = ttk.Frame(result_list_frame)
        result_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(result_buttons, text="导出JSON", command=self.export_json).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(result_buttons, text="清空结果", command=self.clear_results).pack(side=tk.LEFT, padx=(0, 5))
        
        # 下半部分：图形对比区域
        self.image_compare_frame = ttk.LabelFrame(result_tab_paned, text="图形对比", padding="10")
        result_tab_paned.add(self.image_compare_frame, weight=2)
        
        # 创建图形对比区域
        self.setup_image_comparison()
        
        # 绑定结果选择事件
        self.result_tree.bind('<<TreeviewSelect>>', self.on_result_selected)
        
        # 标签页2：图像预览
        preview_tab = ttk.Frame(self.result_notebook)
        self.result_notebook.add(preview_tab, text="图像预览")
        
        # 设置图像预览标签页
        self.setup_image_preview(preview_tab)
    
    def setup_image_preview(self, parent):
        """设置图像预览标签页"""
        # 创建主框架
        preview_frame = ttk.Frame(parent)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 配置网格权重
        preview_frame.columnconfigure(1, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        
        # 核桃选择器
        selection_frame = ttk.LabelFrame(preview_frame, text="核桃选择", padding="10")
        selection_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(selection_frame, text="选择核桃:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.preview_walnut_var = tk.StringVar()
        self.preview_walnut_combo = ttk.Combobox(selection_frame, textvariable=self.preview_walnut_var, width=20)
        self.preview_walnut_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.preview_walnut_combo.bind('<<ComboboxSelected>>', self.on_walnut_selected)
        
        ttk.Button(selection_frame, text="刷新列表", command=self.refresh_walnut_list).grid(row=0, column=2)
        
        # 配置选择框架网格权重
        selection_frame.columnconfigure(1, weight=1)
        
        # 图像显示区域
        image_frame = ttk.LabelFrame(preview_frame, text="多角度图像预览", padding="10")
        image_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(0, weight=1)
        
        # 创建六个角度的图像显示区域
        angles = ['B', 'D', 'F', 'L', 'R', 'T']
        angle_names = ['背面', '底部', '正面', '左侧', '右侧', '顶部']
        
        # 创建图像容器
        self.preview_images = {}
        for i, (angle, name) in enumerate(zip(angles, angle_names)):
            angle_frame = ttk.LabelFrame(image_frame, text=f"{name} ({angle})", padding="5")
            angle_frame.grid(row=i//3, column=i%3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
            
            # 图像标签
            img_label = ttk.Label(angle_frame, text="无图像", width=20, relief="solid")
            img_label.pack(fill=tk.BOTH, expand=True)
            self.preview_images[angle] = img_label
            
            # 图像信息标签
            info_label = ttk.Label(angle_frame, text="", font=("Arial", 8))
            info_label.pack(pady=(5, 0))
            self.preview_images[f"{angle}_info"] = info_label
        
        # 配置图像框架网格权重
        for i in range(3):
            image_frame.columnconfigure(i, weight=1)
        for i in range(2):
            image_frame.rowconfigure(i, weight=1)
        
        # 控制按钮
        control_frame = ttk.Frame(preview_frame)
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(control_frame, text="放大图像", command=self.zoom_in).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(control_frame, text="缩小图像", command=self.zoom_out).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(control_frame, text="重置缩放", command=self.reset_zoom).grid(row=0, column=2, padx=(0, 5))
        
        # 缩放状态标签
        self.zoom_level = 1.0
        self.zoom_label = ttk.Label(control_frame, text=f"缩放: {self.zoom_level:.1f}x")
        self.zoom_label.grid(row=0, column=3, padx=(10, 0))
        
        # 初始化核桃列表
        self.refresh_walnut_list()
    
    def refresh_walnut_list(self):
        """刷新核桃列表"""
        if not self.root_dir_var.get() or not os.path.exists(self.root_dir_var.get()):
            return
        
        try:
            walnut_folders = [f for f in os.listdir(self.root_dir_var.get()) 
                            if os.path.isdir(os.path.join(self.root_dir_var.get(), f))]
            walnut_folders.sort()
            
            self.preview_walnut_combo['values'] = walnut_folders
            
            if walnut_folders and not self.preview_walnut_var.get():
                self.preview_walnut_var.set(walnut_folders[0])
                self.on_walnut_selected()
                
        except Exception as e:
            print(f"刷新核桃列表失败: {e}")
    
    def on_walnut_selected(self, event=None):
        """核桃选择事件处理"""
        selected_walnut = self.preview_walnut_var.get()
        if not selected_walnut:
            return
        
        database_dir = os.path.join(os.path.dirname(__file__), 'walnut_database')
        crop_dir = os.path.join(database_dir, 'crop_images')
        walnut_dir = os.path.join(crop_dir, selected_walnut)
        
        if not os.path.exists(walnut_dir):
            messagebox.showwarning("警告", f"核桃 {selected_walnut} 的裁剪图像不存在")
            return
        
        # 加载并显示六个角度的图像
        angles = ['B', 'D', 'F', 'L', 'R', 'T']
        
        for angle in angles:
            # 查找该角度的图像文件
            angle_files = [f for f in os.listdir(walnut_dir) 
                         if f.endswith(('.jpg', '.png', '.jpeg')) and f'_{angle}_' in f]
            
            if angle_files:
                # 取第一张图像
                img_path = os.path.join(walnut_dir, angle_files[0])
                try:
                    # 加载图像
                    img = Image.open(img_path)
                    
                    # 应用缩放
                    if self.zoom_level != 1.0:
                        new_width = int(img.width * self.zoom_level)
                        new_height = int(img.height * self.zoom_level)
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 调整大小以适应显示区域
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    # 更新图像标签
                    self.preview_images[angle].config(image=photo, text="")
                    self.preview_images[angle].image = photo  # 保存引用
                    
                    # 更新图像信息
                    file_size = os.path.getsize(img_path) / 1024  # KB
                    info_text = f"{img.width}x{img.height} | {file_size:.1f}KB"
                    self.preview_images[f"{angle}_info"].config(text=info_text)
                    
                except Exception as e:
                    print(f"加载图像 {img_path} 失败: {e}")
                    self.preview_images[angle].config(image="", text="加载失败")
                    self.preview_images[f"{angle}_info"].config(text="")
            else:
                self.preview_images[angle].config(image="", text="无图像")
                self.preview_images[f"{angle}_info"].config(text="")
    
    def zoom_in(self):
        """放大图像"""
        self.zoom_level = min(3.0, self.zoom_level + 0.2)
        self.zoom_label.config(text=f"缩放: {self.zoom_level:.1f}x")
        self.on_walnut_selected()
    
    def zoom_out(self):
        """缩小图像"""
        self.zoom_level = max(0.5, self.zoom_level - 0.2)
        self.zoom_label.config(text=f"缩放: {self.zoom_level:.1f}x")
        self.on_walnut_selected()
    
    def reset_zoom(self):
        """重置缩放"""
        self.zoom_level = 1.0
        self.zoom_label.config(text=f"缩放: {self.zoom_level:.1f}x")
        self.on_walnut_selected()
    
    def setup_image_comparison(self):
        """设置图形对比区域"""
        # 清空现有内容
        for widget in self.image_compare_frame.winfo_children():
            widget.destroy()
        
        # 创建主容器，使用网格布局
        main_container = ttk.Frame(self.image_compare_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 配置网格权重
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # 核桃A区域 - 第一行
        walnut_a_frame = ttk.LabelFrame(main_container, text="核桃A: 请选择相似对", padding="10")
        walnut_a_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 核桃A的六个角度图像
        self.walnut_a_images = []
        for i, angle in enumerate(['B', 'D', 'F', 'L', 'R', 'T']):
            angle_frame = ttk.LabelFrame(walnut_a_frame, text=angle, padding="5")
            angle_frame.grid(row=0, column=i, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2)
            
            img_label = ttk.Label(angle_frame, text="无图像", width=15, relief="solid")
            img_label.pack(fill=tk.BOTH, expand=True)
            self.walnut_a_images.append(img_label)
        
        # 配置核桃A框架网格权重
        for i in range(6):
            walnut_a_frame.columnconfigure(i, weight=1)
        
        # 核桃B区域 - 第二行
        walnut_b_frame = ttk.LabelFrame(main_container, text="核桃B: 请选择相似对", padding="10")
        walnut_b_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 核桃B的六个角度图像
        self.walnut_b_images = []
        for i, angle in enumerate(['B', 'D', 'F', 'L', 'R', 'T']):
            angle_frame = ttk.LabelFrame(walnut_b_frame, text=angle, padding="5")
            angle_frame.grid(row=0, column=i, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2)
            
            img_label = ttk.Label(angle_frame, text="无图像", width=15, relief="solid")
            img_label.pack(fill=tk.BOTH, expand=True)
            self.walnut_b_images.append(img_label)
        
        # 配置核桃B框架网格权重
        for i in range(6):
            walnut_b_frame.columnconfigure(i, weight=1)
        
        # 设置图形对比区域的最小高度，确保可见
        self.image_compare_frame.config(height=400)
    
    def on_result_selected(self, event):
        """处理结果选择事件"""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item = self.result_tree.item(selection[0])
        values = item['values']
        
        if len(values) >= 4:
            walnut_a_id = values[1]  # 核桃A的ID
            walnut_b_id = values[2]  # 核桃B的ID
            similarity = values[3]   # 相似度
            
            print(f"选中配对: {walnut_a_id} vs {walnut_b_id}, 相似度: {similarity}")
            
            # 更新标题
            for widget in self.image_compare_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Label) and "核桃" in child.cget("text"):
                            if "核桃A" in child.cget("text"):
                                child.config(text=f"核桃A: {walnut_a_id} (相似度: {similarity})")
                            elif "核桃B" in child.cget("text"):
                                child.config(text=f"核桃B: {walnut_b_id} (相似度: {similarity})")
            
            # 加载并显示图像
            self.load_and_display_images(walnut_a_id, walnut_b_id)
    
    def load_and_display_images(self, walnut_a_id, walnut_b_id):
        """加载并显示核桃图像"""
        database_dir = os.path.join(os.path.dirname(__file__), 'walnut_database')
        crop_dir = os.path.join(database_dir, 'crop_images')
        
        # 确保核桃ID是字符串类型
        walnut_a_id = str(walnut_a_id)
        walnut_b_id = str(walnut_b_id)
        
        # 查找实际的文件夹名称（处理前导零问题）
        def find_actual_folder(walnut_id):
            # 首先尝试直接匹配
            direct_path = os.path.join(crop_dir, walnut_id)
            if os.path.exists(direct_path):
                return walnut_id
            
            # 如果直接匹配失败，尝试查找包含该数字的文件夹
            if os.path.exists(crop_dir):
                for folder in os.listdir(crop_dir):
                    # 去掉前导零后比较
                    folder_clean = folder.lstrip('0')
                    if folder_clean == walnut_id:
                        return folder
            
            # 如果还是找不到，尝试添加前导零
            padded_id = walnut_id.zfill(4)  # 填充到4位
            padded_path = os.path.join(crop_dir, padded_id)
            if os.path.exists(padded_path):
                return padded_id
            
            return None
        
        # 查找实际的文件夹名称
        actual_a_folder = find_actual_folder(walnut_a_id)
        actual_b_folder = find_actual_folder(walnut_b_id)
        
        print(f"查找文件夹: {walnut_a_id} -> {actual_a_folder}, {walnut_b_id} -> {actual_b_folder}")
        
        # 加载核桃A的图像
        if actual_a_folder:
            walnut_a_dir = os.path.join(crop_dir, actual_a_folder)
            self.display_walnut_images(walnut_a_dir, self.walnut_a_images)
        else:
            print(f"❌ 找不到核桃A的文件夹: {walnut_a_id}")
            self.clear_walnut_images(self.walnut_a_images)
        
        # 加载核桃B的图像
        if actual_b_folder:
            walnut_b_dir = os.path.join(crop_dir, actual_b_folder)
            self.display_walnut_images(walnut_b_dir, self.walnut_b_images)
        else:
            print(f"❌ 找不到核桃B的文件夹: {walnut_b_id}")
            self.clear_walnut_images(self.walnut_b_images)
    
    def display_walnut_images(self, walnut_dir, image_labels):
        """显示核桃的六个角度图像"""
        print(f"开始加载核桃图像: {walnut_dir}")
        
        # 按角度加载图像
        angle_images = {}
        for angle in ['B', 'D', 'F', 'L', 'R', 'T']:
            # 查找该角度的图像文件 - 改进搜索逻辑
            angle_files = []
            if os.path.exists(walnut_dir):
                for f in os.listdir(walnut_dir):
                    if f.lower().endswith(('.jpg', '.png', '.jpeg')):
                        # 多种可能的命名模式
                        if f'_{angle}_' in f or f'_{angle}.' in f or f'_{angle}-' in f:
                            angle_files.append(f)
            
            print(f"角度 {angle}: 找到 {len(angle_files)} 个文件")
            
            if angle_files:
                # 取第一张图像
                img_path = os.path.join(walnut_dir, angle_files[0])
                print(f"  加载图像: {img_path}")
                try:
                    # 加载并调整图像大小
                    img = Image.open(img_path)
                    print(f"  图像尺寸: {img.size}")
                    # 调整大小以适应显示区域，保持宽高比
                    img.thumbnail((120, 120), Image.Resampling.LANCZOS)
                    print(f"  缩略图尺寸: {img.size}")
                    photo = ImageTk.PhotoImage(img)
                    angle_images[angle] = photo
                    print(f"  图像加载成功")
                except Exception as e:
                    print(f"Error loading image {img_path}: {e}")
                    angle_images[angle] = None
            else:
                angle_images[angle] = None
                print(f"未找到角度 {angle} 的图像在目录 {walnut_dir}")
        
        # 更新图像标签
        print("更新图像标签...")
        for i, angle in enumerate(['B', 'D', 'F', 'L', 'R', 'T']):
            if angle_images[angle]:
                image_labels[i].config(image=angle_images[angle], text="")
                # 保存引用防止垃圾回收
                image_labels[i].image = angle_images[angle]
                print(f"  角度 {angle}: 图像显示成功")
            else:
                image_labels[i].config(image="", text="无图像")
                print(f"  角度 {angle}: 无图像")
        
        print(f"核桃图像加载完成: {walnut_dir}")
    
    def clear_walnut_images(self, image_labels):
        """清空核桃图像显示"""
        for label in image_labels:
            label.config(image="", text="无图像")
            if hasattr(label, 'image'):
                delattr(label, 'image')
    
    def browse_root_dir(self):
        """浏览核桃根目录"""
        directory = filedialog.askdirectory(title="选择核桃根目录")
        if directory:
            self.root_dir_var.set(directory)
    
    def browse_model_path(self):
        """浏览模型文件"""
        file_path = filedialog.askopenfilename(
            title="选择模型文件",
            filetypes=[("PyTorch模型", "*.pth *.pt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.model_path_var.set(file_path)
    
    def start_processing(self):
        """开始处理"""
        if not self.root_dir_var.get():
            messagebox.showerror("错误", "请选择核桃根目录")
            return
        
        if not os.path.exists(self.root_dir_var.get()):
            messagebox.showerror("错误", "核桃根目录不存在")
            return
        
        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 清空结果和日志
        self.clear_results()
        self.clear_log()
        
        # 启动处理线程
        thread = threading.Thread(target=self.processor.process_walnuts, args=(
            self.root_dir_var.get(),
            self.topk_var.get(),
            self.pca_var.get(),
            self.similarity_var.get(),
            self.cache_var.get(),
            self.force_var.get(),
            self.model_path_var.get() if self.model_path_var.get() else None
        ))
        thread.daemon = True
        thread.start()
    
    def stop_processing(self):
        """停止处理"""
        self.processor.stop_processing()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_text.insert(tk.END, "⏹️ 处理已停止\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def clear_results(self):
        """清空结果"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
    
    def export_json(self):
        """导出JSON结果"""
        if not hasattr(self, 'current_results') or not self.current_results:
            messagebox.showwarning("警告", "没有可导出的结果")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存JSON结果",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_results, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"结果已导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
    
    def show_details(self):
        """显示选中结果的详情"""
        selection = self.result_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个结果")
            return
        
        item = self.result_tree.item(selection[0])
        values = item['values']
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"相似对详情 - {values[1]} vs {values[2]}")
        detail_window.geometry("600x400")
        
        # 显示详细信息
        text = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        detail_text = f"""相似对详情:
排名: {values[0]}
核桃A: {values[1]}
核桃B: {values[2]}
相似度: {values[3]}

特征对比:
- 使用相似度方法: {self.similarity_var.get()}
- Top-K 设置: {self.topk_var.get()}
- PCA维度: {self.pca_var.get()}
"""
        text.insert(tk.END, detail_text)
        text.config(state=tk.DISABLED)
    
    def update_progress(self):
        """更新进度和日志"""
        try:
            while True:
                msg_type, *data = self.processor.progress_queue.get_nowait()
                
                if msg_type == "progress":
                    progress, message = data
                    self.progress_var.set(progress)
                    self.progress_label.config(text=message)
                
                elif msg_type == "log":
                    message = data[0]
                    self.log_text.insert(tk.END, f"{message}\n")
                    self.log_text.see(tk.END)
                
                elif msg_type == "results":
                    results = data[0]
                    self.current_results = results
                    self.display_results(results)
                
                elif msg_type == "error":
                    message = data[0]
                    self.log_text.insert(tk.END, f"❌ {message}\n")
                    self.log_text.see(tk.END)
                    self.start_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                
        except queue.Empty:
            pass
        
        # 继续检查
        self.root.after(100, self.update_progress)
    
    def display_results(self, results):
        """显示结果"""
        self.clear_results()
        
        for rank, (pair_key, pair_data) in enumerate(results.items(), 1):
            walnut_a = pair_data['walnut_a']
            walnut_b = pair_data['walnut_b']
            similarity = pair_data['tensor_similarity']
            
            self.result_tree.insert("", tk.END, values=(
                rank, walnut_a, walnut_b, f"{similarity:.4f}"
            ))
        
        self.log_text.insert(tk.END, f"✅ 结果显示完成，共 {len(results)} 对相似核桃\n")
        self.log_text.see(tk.END)
        
        # 恢复按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # 保存结果数据用于后续图像显示
        self.current_results_data = results


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
        
        print(f"文件夹结构已创建: {database_dir}")
        return True
        
    except Exception as e:
        print(f"文件夹创建失败: {e}")
        return False

def main():
    """主函数"""
    # 首次运行时自动创建必要的文件夹
    create_necessary_folders()
    
    root = tk.Tk()
    app = WalnutGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
