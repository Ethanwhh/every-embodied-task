import habitat
from habitat.sims.habitat_simulator.actions import HabitatSimActions
import cv2


FORWARD_KEY="w"
LEFT_KEY="a"
RIGHT_KEY="d"
FINISH="f"


def transform_rgb_bgr(image):
    """将RGB图像转换为BGR格式（OpenCV使用BGR）"""
    return image[:, :, [2, 1, 0]]


def example():
    """
    交互式导航示例
    """
    # 创建环境
    env = habitat.Env(
        config=habitat.get_config("benchmark/nav/pointnav/pointnav_habitat_test.yaml")
    )

    print("Environment creation successful (环境创建成功)")
    observations = env.reset() # 重置环境
    
    # 打印目标信息
    print("Destination, distance: {:3f}, theta(radians): {:.2f}".format(
        observations["pointgoal_with_gps_compass"][0],
        observations["pointgoal_with_gps_compass"][1]))
    
    # 显示当前观测
    cv2.imshow("RGB", transform_rgb_bgr(observations["rgb"]))

    print("Agent stepping around inside environment (智能体在环境中移动).")

    count_steps = 0
    while not env.episode_over:
        keystroke = cv2.waitKey(0) # 等待按键输入

        if keystroke == ord(FORWARD_KEY):
            action = HabitatSimActions.move_forward
            print("action: FORWARD (前进)")
        elif keystroke == ord(LEFT_KEY):
            action = HabitatSimActions.turn_left
            print("action: LEFT (左转)")
        elif keystroke == ord(RIGHT_KEY):
            action = HabitatSimActions.turn_right
            print("action: RIGHT (右转)")
        elif keystroke == ord(FINISH):
            action = HabitatSimActions.stop
            print("action: FINISH (结束)")
        else:
            print("INVALID KEY (无效按键)")
            continue

        observations = env.step(action) # 执行动作
        count_steps += 1

        # 打印新的目标相对位置
        print("Destination, distance: {:3f}, theta(radians): {:.2f}".format(
            observations["pointgoal_with_gps_compass"][0],
            observations["pointgoal_with_gps_compass"][1]))
        # 更新显示
        cv2.imshow("RGB", transform_rgb_bgr(observations["rgb"]))

    print("Episode finished after {} steps. (Episode在{}步后结束)".format(count_steps))

    if (
        action == HabitatSimActions.stop
        and observations["pointgoal_with_gps_compass"][0] < 0.2
    ):
        print("you successfully navigated to destination point (你已成功导航到目标点)")
    else:
        print("your navigation was unsuccessful (导航未成功)")


if __name__ == "__main__":
    example()