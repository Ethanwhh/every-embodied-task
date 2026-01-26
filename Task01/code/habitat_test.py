import numpy as np  # 数值计算（数组、矩阵操作）
from matplotlib import pyplot as plt  # 绘图库
from PIL import Image  # PIL/Pillow：图像处理（读、写、裁剪等）
import habitat_sim  # Habitat-Sim主库（仿真核心）
from habitat_sim.utils import common as utils  # 通用工具函数（如坐标转换、数据格式处理）
from habitat_sim.utils import viz_utils as vut  # 可视化工具函数（如绘制场景、轨迹）

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
    
    image_name = f"observation_{img_counter}.png"
    plt.savefig(image_name, bbox_inches='tight', pad_inches=0)
    img_counter +=1
    
    plt.show(block=False)
    plt.pause(3)  # 显示3秒（可修改秒数）
    plt.close()

def make_simple_cfg(settings):
    """
    创建简单的仿真配置
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

sim_settings = {
    "scene": test_scene,  # 场景路径
    "default_agent": 0,  # 默认智能体索引
    "sensor_height": 1.5,  # 传感器相对智能体的高度（米）
    "width": 256,  # 观测图像的空间分辨率（宽度）
    "height": 256, # 观测图像的空间分辨率（高度）
}

cfg = make_simple_cfg(sim_settings)
sim = habitat_sim.Simulator(cfg)

agent = sim.initialize_agent(sim_settings["default_agent"])

# 设置智能体状态
agent_state = habitat_sim.AgentState()
agent_state.position = np.array([-0.6, 0.0, 0.0])  # 世界坐标系
agent.set_state(agent_state)

# 获取智能体状态
agent_state = agent.get_state()
print("agent_state: position", agent_state.position, "rotation", agent_state.rotation)

action_names = list(cfg.agents[sim_settings["default_agent"]].action_space.keys())
print("Discrete action space: ", action_names)

def navigateAndSee(action=""):
    if action in action_names:
        observations = sim.step(action)
        print("action: ", action)
        if display:
            display_sample(observations["color_sensor"])


action = "turn_right"
navigateAndSee(action)

action = "turn_right"
navigateAndSee(action)

action = "move_forward"
navigateAndSee(action)

action = "turn_left"
navigateAndSee(action)
