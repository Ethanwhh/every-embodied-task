#!/usr/bin/env python3
import sys
try:
    import habitat_sim
except Exception as e:
    print("import habitat_sim failed:", e)
    sys.exit(2)

scene = "data/scene_datasets/habitat-test-scenes/skokloster-castle.glb"
print("habitat_sim version:", getattr(habitat_sim, "__version__", "unknown"))

# create SimulatorConfiguration
cfg = habitat_sim.SimulatorConfiguration()
print("SimulatorConfiguration attrs before:", [a for a in dir(cfg) if not a.startswith('_')][:50])

# ensure required attributes exist for C++ side
# Some older/newer builds expect cfg.agents to exist (list of AgentConfiguration)
if not hasattr(cfg, "agents"):
    # try to find AgentConfiguration in possible locations
    AgentConfigClass = None
    try:
        AgentConfigClass = getattr(habitat_sim, "AgentConfiguration", None)
    except Exception:
        AgentConfigClass = None
    if AgentConfigClass is None:
        try:
            import habitat_sim.agent as agent_mod
            AgentConfigClass = getattr(agent_mod, "AgentConfiguration", None)
        except Exception:
            AgentConfigClass = None
    if AgentConfigClass is None:
        # last resort: build a minimal dummy with expected attributes
        class AgentConfigDummy:
            def __init__(self):
                self.sensor_specifications = []
        AgentConfigClass = AgentConfigDummy

    # instantiate and set minimal fields
    agent_cfg = AgentConfigClass()
    # try to ensure sensor_specifications exists
    if not hasattr(agent_cfg, "sensor_specifications"):
        agent_cfg.sensor_specifications = []

    cfg.agents = [agent_cfg]
    print("Added minimal cfg.agents with AgentConfiguration:", type(agent_cfg))

# set scene and CPU mode
cfg.scene_id = scene
cfg.gpu_device_id = -1
cfg.enable_physics = False

# attempt to create simulator
try:
    sim = habitat_sim.Simulator(cfg)
    print("场景加载成功（headless CPU 模式）")
    # print some info if available
    try:
        print("Simulator.scene_id:", sim.scene.scene_config.filepath if hasattr(sim.scene, "scene_config") else "unknown")
    except Exception:
        pass
    sim.close()
except Exception as e:
    import traceback
    print("加载场景失败，异常：", repr(e))
    traceback.print_exc()
    sys.exit(1)
