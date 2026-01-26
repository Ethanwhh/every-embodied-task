import os
from typing import TYPE_CHECKING, Union, cast

import git
import matplotlib.pyplot as plt
import numpy as np

import habitat
from habitat.config.default_structured_configs import (
    CollisionsMeasurementConfig,
    FogOfWarConfig,
    TopDownMapMeasurementConfig,
)
from habitat.core.agent import Agent
from habitat.tasks.nav.nav import NavigationEpisode, NavigationGoal
from habitat.tasks.nav.shortest_path_follower import ShortestPathFollower
from habitat.utils.visualizations import maps
from habitat.utils.visualizations.utils import (
    images_to_video,
    observations_to_image,
    overlay_frame,
)
from habitat_sim.utils import viz_utils as vut

# 禁用Habitat模拟器日志输出
os.environ["MAGNUM_LOG"] = "quiet"
os.environ["HABITAT_SIM_LOG"] = "quiet"

if TYPE_CHECKING:
    from habitat.core.simulator import Observations
    from habitat.sims.habitat_simulator.habitat_simulator import HabitatSim

output_path = "./code"
os.makedirs(output_path, exist_ok=True)

class ShortestPathFollowerAgent(Agent):
    r"""实现了 :ref:`habitat.core.agent.Agent` 接口的智能体，
    使用 :ref`habitat.tasks.nav.shortest_path_follower.ShortestPathFollower` 工具类
    来提取通往目标的最短路径动作。
    """

    def __init__(self, env: habitat.Env, goal_radius: float):
        self.env = env
        self.shortest_path_follower = ShortestPathFollower(
            sim=cast("HabitatSim", env.sim),
            goal_radius=goal_radius,
            return_one_hot=False,
        )

    def act(self, observations: "Observations") -> Union[int, np.ndarray]:
        return self.shortest_path_follower.get_next_action(
            cast(NavigationEpisode, self.env.current_episode).goals[0].position
        )

    def reset(self) -> None:
        pass


def example_top_down_map_measure():
    """
    演示顶视图地图测量指标的配置和使用，并生成视频
    """
    # 创建habitat配置
    config = habitat.get_config(
        config_path="benchmark/nav/pointnav/pointnav_habitat_test.yaml"
    )
    # 添加顶视图地图(TopDownMap)和碰撞(Collisions)测量指标
    with habitat.config.read_write(config):
        config.habitat.task.measurements.update(
            {
                "top_down_map": TopDownMapMeasurementConfig(
                    map_padding=3,
                    map_resolution=1024,
                    draw_source=True,
                    draw_border=True,
                    draw_shortest_path=True,
                    draw_view_points=True,
                    draw_goal_positions=True,
                    draw_goal_aabbs=True,
                    fog_of_war=FogOfWarConfig(
                        draw=True,
                        visibility_dist=5.0,
                        fov=90,
                    ),
                ),
                "collisions": CollisionsMeasurementConfig(),
            }
        )
    # 创建数据集
    dataset = habitat.make_dataset(
        id_dataset=config.habitat.dataset.type, config=config.habitat.dataset
    )
    # 创建仿真环境
    with habitat.Env(config=config, dataset=dataset) as env:
        # 创建最短路径跟随者智能体
        agent = ShortestPathFollowerAgent(
            env=env,
            goal_radius=config.habitat.task.measurements.success.success_distance,
        )
        # 录制智能体在第一个episode中导航的视频
        num_episodes = 1
        for _ in range(num_episodes):
            # 加载第一个episode并重置智能体
            observations = env.reset()
            agent.reset()

            # 获取指标
            info = env.get_metrics()
            # 将RGB-D观测和顶视图地图合并为一张图像
            frame = observations_to_image(observations, info)

            # 从指标中移除top_down_map以便叠加其他文本信息
            info.pop("top_down_map")
            # 将数值指标叠加到帧上
            frame = overlay_frame(frame, info)
            # 添加帧到vis_frames列表
            vis_frames = [frame]

            # 循环直到智能体到达目标或episode结束
            while not env.episode_over:
                # 获取下一个最佳动作
                action = agent.act(observations)
                if action is None:
                    break

                # 执行动作
                observations = env.step(action)
                info = env.get_metrics()
                frame = observations_to_image(observations, info)

                info.pop("top_down_map")
                frame = overlay_frame(frame, info)
                vis_frames.append(frame)

            current_episode = env.current_episode
            video_name = f"{os.path.basename(current_episode.scene_id)}_{current_episode.episode_id}"
            # 将图像序列转换为视频保存到磁盘
            images_to_video(
                vis_frames, output_path, video_name, fps=6, quality=9
            )
            vis_frames.clear()
            # 显示视频（如果运行在支持显示环境）
            vut.display_video(f"{output_path}/{video_name}.mp4")

if __name__ == "__main__":
    example_top_down_map_measure()