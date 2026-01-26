import os
import imageio  # 处理图像/视频（读、写、帧合成）
import numpy as np  # 数值计算（数组、矩阵操作）
import scipy.ndimage as ndimage
from matplotlib import pyplot as plt  # 绘图库

import habitat_sim  # Habitat-Sim主库（仿真核心）
from habitat_sim.utils import common as utils  # 通用工具函数（如坐标转换、数据格式处理）
from habitat_sim.utils import viz_utils as vut  # 可视化工具函数（如绘制场景、轨迹）

def make_cfg(settings):
    """
    创建仿真器配置对象
    
    参数:
    settings (dict): 包含配置参数的字典
    
    返回:
    habitat_sim.Configuration: 配置好的仿真器配置对象
    """
    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.gpu_device_id = 0
    sim_cfg.scene_id = settings["scene"] # 场景ID（文件路径）
    sim_cfg.enable_physics = settings["enable_physics"] # 是否开启物理引擎

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



def display_map(topdown_map, key_points=None):
    """
    显示顶视图地图，并可选地绘制关键点
    
    参数:
    topdown_map: 地图数据（2D数组）
    key_points: 可选的关键点列表，将在地图上绘制为圆点
    """
    global img_counter
    plt.figure(figsize=(12, 8))
    ax = plt.subplot(1, 1, 1)
    ax.axis("off")
    plt.imshow(topdown_map)
    # 在地图上绘制点
    if key_points is not None:
        for point in key_points:
            plt.plot(point[0], point[1], marker="o", markersize=10, alpha=0.8)
    
    image_name = f"navmesh_{img_counter}.png"
    plt.savefig(image_name, bbox_inches='tight', pad_inches=0)
    img_counter +=1
    plt.show(block=False)
    plt.pause(3)  # 显示3秒（可修改秒数）
    plt.close()



def get_topdown_map(pathfinder, height, meters_per_pixel) -> np.ndarray:
    """
    获取指定高度的顶视图导航网格地图
    
    参数:
    pathfinder: 导航网格对象
    height: 切片高度
    meters_per_pixel: 每个像素代表的米数（分辨率）
    
    返回:
    np.ndarray: 生成的地图，0=不可导航，1=可导航，2=边界
    """
    # 获取场景的导航边界（x, z轴，忽略y轴高度）
    bounds = pathfinder.get_bounds()
    min_x, _, min_z = bounds[0]
    max_x, _, max_z = bounds[1]

    # 计算地图的像素尺寸（x对应宽度，z对应高度）
    map_width = int(np.ceil((max_x - min_x) / meters_per_pixel))
    map_height = int(np.ceil((max_z - min_z) / meters_per_pixel))

    # 初始化地图：0=不可导航，1=可导航
    topdown_map = np.zeros((map_height, map_width), dtype=np.uint8)

    # 遍历每个像素，判断是否可导航（优化：用向量化操作替代双重循环，提升速度）
    x_coords = np.linspace(min_x, max_x, map_width, endpoint=False)
    z_coords = np.linspace(min_z, max_z, map_height, endpoint=False)
    x_grid, z_grid = np.meshgrid(x_coords, z_coords)
    # 构造(x, height, z)的坐标数组
    world_coords = np.stack([x_grid.ravel(), np.full_like(x_grid.ravel(), height), z_grid.ravel()], axis=1)
    # 批量判断是否可导航
    navigable = np.array([pathfinder.is_navigable(coord) for coord in world_coords])
    # 重塑为地图尺寸
    topdown_map = navigable.reshape((map_height, map_width)).astype(np.uint8)

    # 计算边界（可选，匹配旧版本的2值）
    edges = ndimage.laplace(topdown_map) != 0
    topdown_map[edges] = 2

    return topdown_map

display = True 
test_scene = "../data/scene_datasets/mp3d_example/17DRP5sb8fy/17DRP5sb8fy.glb"

rgb_sensor = True 
depth_sensor = True
semantic_sensor = True 
img_counter = 0

# 仿真设置字典
sim_settings = {
    "width": 256,  # 观测图像的空间分辨率（宽度）
    "height": 256, # 观测图像的空间分辨率（高度）
    "scene": test_scene,  # 场景路径
    "default_agent": 0, # 默认智能体ID
    "sensor_height": 1.5,  # 传感器高度（米）
    "color_sensor": rgb_sensor,  # RGB传感器开关
    "depth_sensor": depth_sensor,  # 深度传感器开关
    "semantic_sensor": semantic_sensor,  # 语义传感器开关
    "seed": 1,  # 用于随机导航的随机种子
    "enable_physics": False,  # 仅运动学模拟
}

cfg = make_cfg(sim_settings)
sim = habitat_sim.Simulator(cfg) # 初始化仿真器
meters_per_pixel = 0.12 # 地图分辨率
custom_height = False
height = 1


print("The NavMesh bounds are: " + str(sim.pathfinder.get_bounds()))
if not custom_height:
    # 获取包围盒最小高度作为自动高度
    height = sim.pathfinder.get_bounds()[0][1]

if not sim.pathfinder.is_loaded:
    print("Pathfinder not initialized, aborting.")
else:
    # 使用Habitat内置方法获取顶视图（如果有）
    sim_topdown_map = sim.pathfinder.get_topdown_view(meters_per_pixel, height)

    if display:
        # 使用自定义函数获取顶视图
        hablab_topdown_map = get_topdown_map(
            sim.pathfinder, height, meters_per_pixel=meters_per_pixel
        )
        # 重新着色地图以便显示
        recolor_map = np.array(
            [[255, 255, 255], [128, 128, 128], [0, 0, 0]], dtype=np.uint8
        )
        hablab_topdown_map = recolor_map[hablab_topdown_map]
        display_map(sim_topdown_map)
        display_map(hablab_topdown_map)
