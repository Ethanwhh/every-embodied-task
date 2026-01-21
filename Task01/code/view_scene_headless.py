#!/usr/bin/env python3
import sys
try:
    import habitat_sim
except Exception as e:
    print("import habitat_sim failed:", e); sys.exit(2)
scene = "data/scene_datasets/habitat-test-scenes/skokloster-castle.glb"
print("habitat_sim version:", habitat_sim.__version__)
cfg = habitat_sim.SimulatorConfiguration()
cfg.scene_id = scene
cfg.gpu_device_id = -1
cfg.enable_physics = False
try:
    sim = habitat_sim.Simulator(cfg)
    print("场景加载成功（headless CPU 模式）")
    sim.close()
except Exception as e:
    print("加载场景失败，异常：", repr(e)); sys.exit(1)
