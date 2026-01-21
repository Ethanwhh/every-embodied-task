# Habitat-sim环境搭建及基础实践

## 环境搭建

创建conda环境（推荐在ubuntu22.04或者ubuntu24.04）

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
``