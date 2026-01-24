import torch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import os
import time

# --- 模型导入 ---
from transformers import DPTImageProcessor, DPTForDepthEstimation
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"使用设备: {device}")

# --- 辅助函数：显示并保存结果 ---
def save_visualization(image, mask_or_depth, mode="sam", output_name="output.png"):
    plt.figure(figsize=(12, 8))
    
    if mode == "depth":
        # 并排显示：原图 vs 深度图
        plt.subplot(1, 2, 1)
        plt.imshow(image)
        plt.title("Original Image")
        plt.axis('off')
        
        plt.subplot(1, 2, 2)
        plt.imshow(mask_or_depth, cmap="inferno")
        plt.colorbar(label="Relative Depth")
        plt.title("Depth Estimation")
        plt.axis('off')

    elif mode == "sam":
        # 叠加显示 SAM Mask
        plt.imshow(image)
        ax = plt.gca()
        ax.set_autoscale_on(False)
        
        # 将 Mask 按面积排序，大的在下，小的在上
        sorted_anns = sorted(mask_or_depth, key=(lambda x: x['area']), reverse=True)
        
        img_overlay = np.ones((sorted_anns[0]['segmentation'].shape[0], sorted_anns[0]['segmentation'].shape[1], 4))
        img_overlay[:,:,3] = 0 # 透明度初始化
        
        for ann in sorted_anns:
            m = ann['segmentation']
            color_mask = np.concatenate([np.random.random(3), [0.4]]) # 随机颜色 + 0.4 透明度
            img_overlay[m] = color_mask
        ax.imshow(img_overlay)
        plt.title("SAM Segmentation")
        plt.axis('off')
    
    plt.savefig(output_name, bbox_inches='tight')
    plt.close()
    print(f"结果已保存至: {output_name}")

# --- 主流程 ---
def main():
    # 1. 路径设置
    rgb_path = "test_image.png" # 替换为图片
    #sam_ckpt = "sam_vit_h_4b8939.pth"

    # 使用小模型以节省资源
    sam_ckpt = "sam_vit_b_01ec64.pth"

    if not os.path.exists(rgb_path):
        print(f"错误: 找不到图片 {rgb_path}")
        return

    # 加载图片
    image_pil = Image.open(rgb_path).convert("RGB")
    image_np = np.array(image_pil)

    # ---------------------------------------------------------
    # 任务 1: 深度估计 (Depth Estimation)
    # ---------------------------------------------------------
    print("\n--- [1/2] 正在运行深度估计 ---")
    try:
        depth_processor = DPTImageProcessor.from_pretrained("Intel/dpt-large")
        depth_model = DPTForDepthEstimation.from_pretrained("Intel/dpt-large").to(device)
        
        inputs = depth_processor(images=image_pil, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = depth_model(**inputs)
            predicted_depth = outputs.predicted_depth
            
        # 插值还原尺寸
        prediction = torch.nn.functional.interpolate(
            predicted_depth.unsqueeze(1),
            size=image_pil.size[::-1],
            mode="bicubic",
            align_corners=False,
        ).squeeze().cpu().numpy()
        
        # 保存深度图结果
        save_visualization(image_np, prediction, mode="depth", output_name="result_01_depth.png")
        
    except Exception as e:
        print(f"深度估计失败: {e}")

    # ---------------------------------------------------------
    # 任务 2: SAM 全图分割 (Segment Anything)
    # ---------------------------------------------------------
    print("\n--- [2/2] 正在运行 SAM 分割 ---")
    if os.path.exists(sam_ckpt):
        try:
            sam = sam_model_registry["vit_b"](checkpoint=sam_ckpt).to(device)
            mask_generator = SamAutomaticMaskGenerator(sam)
            masks = mask_generator.generate(image_np)
            
            # 保存 SAM 结果 (注意文件名不同，避免覆盖)
            save_visualization(image_np, masks, mode="sam", output_name="result_02_sam_seg.png")
            
        except Exception as e:
            print(f"SAM 分割失败: {e}")
    else:
        print(f"跳过 SAM: 未找到权重文件 {sam_ckpt}")

if __name__ == "__main__":
    main()
