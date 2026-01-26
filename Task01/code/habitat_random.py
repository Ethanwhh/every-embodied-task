import math
import os
import random
import sys

import imageio  # 处理图像/视频（读、写、帧合成）
import magnum as mn  # 3D图形/线性代数库（Habitat-Sim依赖）
import numpy as np  # 数值计算（数组、矩阵操作）

from matplotlib import pyplot as plt  # 绘图库

from PIL import Image  # PIL/Pillow：图像处理（读、写、裁剪等）
import habitat_sim  # Habitat-Sim主库（仿真核心）
from habitat_sim.utils import common as utils  # 通用工具函数（如坐标转换、数据格式处理）
from habitat_sim.utils import viz_utils as vut  # 可视化工具函数（如绘制场景、轨迹）
# from habitat_sim.utils.visualizations import maps

img_counter = 0
def display_sample(rgb_obs, semantic_obs=np.array([]), depth_obs=np.array([])):
    """
    显示观测样本（RGB、语义分割、深度图）
    """
    from habitat_sim.utils.common import d3_40_colors_rgb

    rgb_img = Image.fromarray(rgb_obs, mode="RGBA")
    global img_counter

    arr = [rgb_img]
    titles = ["rgb"]
    if semantic_obs.size != 0:
        semantic_img = Image.new("P", (semantic_obs.shape[1], semantic_obs.shape[0]))
        semantic_img.putpalette(d3_40_colors_rgb.flatten())
        semantic_img.putdata((semantic_obs.flatten() % 40).astype(np.uint8))
        semantic_img = semantic_img.convert("RGBA")
        arr.append(semantic_img)
        titles.append("semantic")

    if depth_obs.size != 0:
        depth_img = Image.fromarray((depth_obs / 10 * 255).astype(np.uint8), mode="L")
        arr.append(depth_img)
        titles.append("depth")

    plt.figure(figsize=(12, 8))
    for i, data in enumerate(arr):
        ax = plt.subplot(1, 3, i + 1)
        ax.axis("off")
        ax.set_title(titles[i])
        plt.imshow(data)
    
    image_name = f"randomtest_{img_counter}.png"
    plt.savefig(image_name, bbox_inches='tight', pad_inches=0)
    img_counter +=1
    
    plt.show(block=False)
    plt.pause(3)  # 显示3秒（可修改秒数）
    plt.close()

def make_simple_cfg(settings):
    """
    创建简单的仿真配置（仅RGB传感器）
    """
    # 仿真器后端配置
    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = settings["scene"]

    # 智能体配置
    agent_cfg = habitat_sim.agent.AgentConfiguration()

    # 在第一个例子中，我们只给智能体附加一个RGB视觉传感器
    rgb_sensor_spec = habitat_sim.CameraSensorSpec()
    rgb_sensor_spec.uuid = "color_sensor"
    rgb_sensor_spec.sensor_type = habitat_sim.SensorType.COLOR
    rgb_sensor_spec.resolution = [settings["height"], settings["width"]]
    rgb_sensor_spec.position = habitat_sim.geo.UP * settings["sensor_height"]
    rgb_sensor_spec.position = [0.0, settings["sensor_height"], 0.0]

    agent_cfg.sensor_specifications = [rgb_sensor_spec]

    return habitat_sim.Configuration(sim_cfg, [agent_cfg])

display = True 

test_scene = "../data/scene_datasets/mp3d_example/17DRP5sb8fy/17DRP5sb8fy.glb"
mp3d_scene_dataset = "../data/scene_datasets/mp3d_example/mp3d.scene_dataset_config.json"

rgb_sensor = True
depth_sensor = True
semantic_sensor = True 

sim_settings = {
    "width": 256,  # 观测图像的空间分辨率（宽度）
    "height": 256, # 观测图像的空间分辨率（高度）
    "scene": test_scene,  # 场景路径
    "scene_dataset": mp3d_scene_dataset, # 场景数据集配置
    "default_agent": 0, # 默认智能体ID
    "sensor_height": 1.5,  # 传感器高度（米）
    "color_sensor": rgb_sensor,  # RGB传感器开关
    "depth_sensor": depth_sensor,  # 深度传感器开关
    "semantic_sensor": semantic_sensor,  # 语义传感器开关
    "seed": 1,  # 用于随机导航的随机种子
    "enable_physics": False,  # 仅运动学模拟
}

def make_cfg(settings):
    """
    创建完整的仿真配置（多传感器）
    """
    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.gpu_device_id = 0
    sim_cfg.scene_id = settings["scene"]
    sim_cfg.scene_dataset_config_file = settings["scene_dataset"]
    sim_cfg.enable_physics = settings["enable_physics"]

    # 注意：所有传感器必须具有相同的分辨率
    sensors = {
        "color_sensor": {
            "sensor_type": habitat_sim.SensorType.COLOR,
            "resolution": [settings["height"], settings["width"]],
            "position": [0.0, settings["sensor_height"], 0.0],
        },
        "depth_sensor": {
            "sensor_type": habitat_sim.SensorType.DEPTH,
            "resolution": [settings["height"], settings["width"]],
            "position": [0.0, settings["sensor_height"], 0.0],
        },
        "semantic_sensor": {
            "sensor_type": habitat_sim.SensorType.SEMANTIC,
            "resolution": [settings["height"], settings["width"]],
            "position": [0.0, settings["sensor_height"], 0.0],
        },
    }

    sensor_specs = []
    for sensor_uuid, sensor_params in sensors.items():
        if settings[sensor_uuid]:
            sensor_spec = habitat_sim.CameraSensorSpec()
            sensor_spec.uuid = sensor_uuid
            sensor_spec.sensor_type = sensor_params["sensor_type"]
            sensor_spec.resolution = sensor_params["resolution"]
            sensor_spec.position = sensor_params["position"]

            sensor_specs.append(sensor_spec)

    # 在这里可以指定前进动作的位移量和转向角度
    agent_cfg = habitat_sim.agent.AgentConfiguration()
    agent_cfg.sensor_specifications = sensor_specs
    agent_cfg.action_space = {
        "move_forward": habitat_sim.agent.ActionSpec(
            "move_forward", habitat_sim.agent.ActuationSpec(amount=0.25)
        ),
        "turn_left": habitat_sim.agent.ActionSpec(
            "turn_left", habitat_sim.agent.ActuationSpec(amount=30.0)
        ),
        "turn_right": habitat_sim.agent.ActionSpec(
            "turn_right", habitat_sim.agent.ActuationSpec(amount=30.0)
        ),
    }

    return habitat_sim.Configuration(sim_cfg, [agent_cfg])

cfg = make_cfg(sim_settings)
sim = habitat_sim.Simulator(cfg)
def print_scene_recur(scene, limit_output=10):
    """
    递归打印场景图信息（层级、区域、物体）
    """
    print(
        f"House has {len(scene.levels)} levels, {len(scene.regions)} regions and {len(scene.objects)} objects"
    )
    print(f"House center:{scene.aabb.center} dims:{scene.aabb.sizes}")

    count = 0
    for level in scene.levels:
        print(
            f"Level id:{level.id}, center:{level.aabb.center},"
            f" dims:{level.aabb.sizes}"
        )
        for region in level.regions:
            print(
                f"Region id:{region.id}, category:{region.category.name()},"
                f" center:{region.aabb.center}, dims:{region.aabb.sizes}"
            )
            for obj in region.objects:
                print(
                    f"Object id:{obj.id}, category:{obj.category.name()},"
                    f" center:{obj.aabb.center}, dims:{obj.aabb.sizes}"
                )
                count += 1
                if count >= limit_output:
                    return None
                
scene = sim.semantic_scene
print_scene_recur(scene)
random.seed(sim_settings["seed"])
sim.seed(sim_settings["seed"])

# 设置智能体状态
agent = sim.initialize_agent(sim_settings["default_agent"])
agent_state = habitat_sim.AgentState()
agent_state.position = np.array([-0.6, 0.0, 0.0])  # 世界坐标系
agent.set_state(agent_state)

# 获取智能体状态
agent_state = agent.get_state()
print("agent_state: position", agent_state.position, "rotation", agent_state.rotation)

total_frames = 0
action_names = list(cfg.agents[sim_settings["default_agent"]].action_space.keys())

max_frames = 5

while total_frames < max_frames:
    action = random.choice(action_names)
    print("action", action)
    observations = sim.step(action)
    rgb = observations["color_sensor"]
    semantic = observations["semantic_sensor"]
    depth = observations["depth_sensor"]

    if display:
        display_sample(rgb, semantic, depth)

    total_frames += 1
