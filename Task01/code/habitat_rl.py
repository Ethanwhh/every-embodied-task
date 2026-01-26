#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import shutil

import numpy as np

import habitat
from habitat.tasks.nav.shortest_path_follower import ShortestPathFollower
from habitat.utils.visualizations import maps
from habitat.utils.visualizations.utils import images_to_video

IMAGE_DIR = os.path.dirname(os.path.abspath(__file__)) # 当前文件目录


class SimpleRLEnv(habitat.RLEnv):
    """
    简单的强化学习环境，继承自habitat.RLEnv
    """
    def get_reward_range(self):
        """定义奖励范围"""
        return [-1, 1]

    def get_reward(self, observations):
        """计算奖励（当前示例返回固定值0）"""
        return 0

    def get_done(self, observations):
        """判断当前episode是否结束"""
        return self.habitat_env.episode_over

    def get_info(self, observations):
        """获取环境信息"""
        return self.habitat_env.get_metrics()


def draw_top_down_map(info, output_size):
    """
    绘制顶视图地图并调整大小
    
    参数:
    info (dict): 包含top_down_map及其他信息的字典
    output_size (int): 输出图像的高度
    """
    return maps.colorize_draw_agent_and_fit_to_height(
        info["top_down_map"], output_size
    )


def shortest_path_example():
    """
    最短路径导航示例
    """
    # 获取默认配置，并覆盖部分参数以启用顶视图地图
    config = habitat.get_config(
        config_path="benchmark/nav/pointnav/pointnav_habitat_test.yaml",
        overrides=[
            "+habitat/task/measurements@habitat.task.measurements.top_down_map=top_down_map"
        ],
    )

    with SimpleRLEnv(config=config) as env:
        # 目标半径
        goal_radius = env.episodes[0].goals[0].radius
        if goal_radius is None:
            goal_radius = config.habitat.simulator.forward_step_size
        
        # 初始化最短路径跟随者
        follower = ShortestPathFollower(
            env.habitat_env.sim, goal_radius, False
        )

        print("Environment creation successful (环境创建成功)")
        for episode in range(3): # 运行3个episode
            env.reset()
            dirname = os.path.join(
                IMAGE_DIR, "shortest_path_example", "%02d" % episode
            )
            if os.path.exists(dirname):
                shutil.rmtree(dirname)
            os.makedirs(dirname)
            print("Agent stepping around inside environment (智能体在环境中移动).")
            images = []
            while not env.habitat_env.episode_over:
                # 获取下一步的最优动作
                best_action = follower.get_next_action(
                    env.habitat_env.current_episode.goals[0].position
                )
                if best_action is None:
                    break

                # 执行动作
                observations, reward, done, info = env.step(best_action)
                im = observations["rgb"]
                
                # 绘制地图并拼接
                top_down_map = draw_top_down_map(info, im.shape[0])
                output_im = np.concatenate((im, top_down_map), axis=1)
                images.append(output_im)
            
            # 生成视频
            images_to_video(images, dirname, "trajectory")
            print("Episode finished")


def main():
    shortest_path_example()


if __name__ == "__main__":
    main()