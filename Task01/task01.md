# Habitat-sim环境搭建及基础实践

## 环境搭建

### 创建conda环境

```bash
conda create -n habitat python=3.9 cmake=3.14.0
conda activate habitat
```

1）在自己的电脑上运行或者服务器在自己身边，有显示器的情况，推荐安装带有物理模拟的habitat-sim

```bash
conda install habitat-sim=0.2.5 withbullet -c conda-forge -c aihabitat
```

2）在自己的电脑上运行或者服务器在自己身边，有显示器的情况，也可以安装不带物理模拟的habitat-sim

```bash
conda install habitat-sim=0.2.5 -c conda-forge -c aihabitat
```

3）在租的服务器上，没有显示器的电脑上运行时，使用headless的habitat-sim（带有物理模拟的安装）

```bash
conda install habitat-sim=0.2.5 withbullet headless -c conda-forge -c aihabitat
```

4）在租的服务器上，没有显示器的电脑上运行时，使用headless的habitat-sim（没有物理模拟的安装）

```bash
conda install habitat-sim=0.2.5 -c conda-forge -c aihabitat
```

### 下载 3D 测试场景和示例对象

下载 3D 测试场景

```bash
python -m habitat_sim.utils.datasets_download --uids habitat_test_scenes --data-path data/
```

下载示例对象

```bash
python -m habitat_sim.utils.datasets_download --uids habitat_example_objects --data-path data/
```

### 进行测试

```bash
habitat-viewer data/scene_datasets/habitat-test-scenes/skokloster-castle.glb
```

出现报错：

![](img/01.png)

运行 habitat-sim 并不一定需要 imageio-ffmpeg 依赖项，该软件包依赖于 libva ，而 libva 又依赖于 libgl 、 libglx 、 libegl 和 libglvnd ，最后这 4 个软件包可能与 Linux 软件包冲突，导致 OpenGL 前端库无法与 OpenGL 后端通信，只要卸载conda环境中这四个包就好了。参考链接：https://github.com/facebookresearch/habitat-sim/pull/2519

![](img/02.png)
![](img/03.png)

卸载后再次测试：

![](img/04.png)

测试成功！
