import numpy as np
import torch
import cv2
import matplotlib.pyplot as plt
from segment_anything import sam_model_registry, SamPredictor
from transformers import DPTImageProcessor, DPTForDepthEstimation
from PIL import Image
import os

# --- 配置 ---
# 请确保下载了权重文件: sam_vit_h_4b8939.pth
#SAM_CHECKPOINT = "sam_vit_h_4b8939.pth" 
#MODEL_TYPE = "vit_h"

# 改用 Base 模型以节省显存
SAM_CHECKPOINT = "sam_vit_b_01ec64.pth"
MODEL_TYPE = "vit_b"

DEPTH_MODEL_NAME = "Intel/dpt-large"
IMAGE_PATH = "test_image.png"  # 替换为你的本地图片路径

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Running on device: {device}")

# --- 1. 模型加载 ---
print("Loading Depth Model...")
depth_processor = DPTImageProcessor.from_pretrained(DEPTH_MODEL_NAME)
depth_model = DPTForDepthEstimation.from_pretrained(DEPTH_MODEL_NAME).to(device)
depth_model.eval()

print("Loading SAM Model...")
if not os.path.exists(SAM_CHECKPOINT):
    raise FileNotFoundError(f"SAM checkpoint not found at {SAM_CHECKPOINT}. Please download it first.")
sam = sam_model_registry[MODEL_TYPE](checkpoint=SAM_CHECKPOINT)
sam.to(device=device)
predictor = SamPredictor(sam)

# --- 2. 核心处理函数 ---
def get_depth_map(image_pil):
    """生成全图的相对深度图"""
    inputs = depth_processor(images=image_pil, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = depth_model(**inputs)
        predicted_depth = outputs.predicted_depth
    
    # 插值到原图尺寸
    prediction = torch.nn.functional.interpolate(
        predicted_depth.unsqueeze(1),
        size=image_pil.size[::-1],
        mode="bicubic",
        align_corners=False,
    )
    return prediction.squeeze().cpu().numpy()

# --- 3. 交互逻辑 ---
def interactive_demo():
    # 读取图像
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image {IMAGE_PATH} not found.")
        return

    image_cv = cv2.imread(IMAGE_PATH)
    image_cv = cv2.resize(image_cv, (1024, int(1024 * image_cv.shape[0] / image_cv.shape[1]))) # 调整大小以免屏幕放不下
    image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
    image_pil = Image.fromarray(image_rgb)
    
    # 预计算深度图
    print("Computing depth map...")
    depth_map = get_depth_map(image_pil)
    
    # 初始化 SAM
    print("Setting image for SAM...")
    predictor.set_image(image_rgb)

    # 状态变量
    input_point = []
    input_label = []
    current_mask = None
    
    print("\n--- 操作指南 ---")
    print("左键: 点击选择物体 (前景)")
    print("右键: 点击排除区域 (背景)")
    print("R键: 重置选择")
    print("Q键: 退出")

    def mouse_callback(event, x, y, flags, param):
        nonlocal input_point, input_label, current_mask
        
        if event == cv2.EVENT_LBUTTONDOWN:
            input_point.append([x, y])
            input_label.append(1) # 1 表示前景
        elif event == cv2.EVENT_RBUTTONDOWN:
            input_point.append([x, y])
            input_label.append(0) # 0 表示背景
        else:
            return

        # 调用 SAM 预测
        masks, scores, _ = predictor.predict(
            point_coords=np.array(input_point),
            point_labels=np.array(input_label),
            multimask_output=False
        )
        current_mask = masks[0]
        
        # 计算深度统计
        # 提取 Mask 区域对应的深度值
        masked_depth = depth_map[current_mask]
        if masked_depth.size > 0:
            avg_depth = np.mean(masked_depth)
            print(f"Object Depth -> Mean: {avg_depth:.4f} (Score: {scores[0]:.3f})")

    cv2.namedWindow("SAM + Depth Interaction", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("SAM + Depth Interaction", mouse_callback)

    while True:
        display_img = image_cv.copy()

        # 绘制点击点
        for pt, label in zip(input_point, input_label):
            color = (0, 255, 0) if label == 1 else (0, 0, 255)
            cv2.circle(display_img, tuple(pt), 5, color, -1)

        # 绘制 Mask 叠加
        if current_mask is not None:
            # 创建红色半透明遮罩
            colored_mask = np.zeros_like(display_img)
            colored_mask[current_mask] = [0, 0, 255] # BGR format
            display_img = cv2.addWeighted(display_img, 1, colored_mask, 0.5, 0)
            
            # 绘制轮廓
            contours, _ = cv2.findContours(current_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(display_img, contours, -1, (255, 255, 255), 2)

        cv2.imshow("SAM + Depth Interaction", display_img)
        
        key = cv2.waitKey(50) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            input_point = []
            input_label = []
            current_mask = None
            print("Reset.")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    interactive_demo()
