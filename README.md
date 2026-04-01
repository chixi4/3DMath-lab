# 3DMath-lab

## 项目简介

`3DMath-lab` 是一个把二维面积微元、旋转体切片和相机运动设计放进同一条动画管线里的公开研究仓。
这个仓库同时保留三层内容：

- 最终版动画主线
- 早期的 ManimCE / ManimGL 原型与实验脚本
- 相机与关键帧编辑工具

如果你只想看最终结果，直接看 [`assets/final/`](assets/final/) 和下面的三条主命令就够了。

## 最终成片

- Canonical final: [`assets/final/volume-of-revolution-final-1080p60.mp4`](assets/final/volume-of-revolution-final-1080p60.mp4)
- Final frame: [`assets/final/volume-of-revolution-final-frame.png`](assets/final/volume-of-revolution-final-frame.png)
- Cover frame: [`assets/final/volume-of-revolution-cover.png`](assets/final/volume-of-revolution-cover.png)

![Cover](assets/final/volume-of-revolution-cover.png)

最终版采用黑色背景、`1080p / 60fps` 输出，并以 freeze-end 结尾为唯一正式版本。

## 最终版生成链路

最终视频通过三步生成：

1. `render-final-source.sh`
   生成带 differential 节奏和相机设计的 ManimGL 源视频。
2. `render-final-overlay.sh`
   在现有渲染上叠加 linked rectangles 矩形层，形成最终前一版。
3. `render-final-video.sh`
   把结尾收成 freeze-end 版本，得到 canonical final。

更完整的链路说明见 [`docs/final-pipeline.md`](docs/final-pipeline.md)。

## 仓库结构

```text
assets/final/              最终成片与精选静帧
config/                    渲染配置
docs/                      项目说明与研究记录
scripts/setup/             环境搭建脚本
scripts/render/            最终成片与原型渲染入口
scripts/analysis/          批处理、对比与分析工具
scripts/windows/           Windows 辅助脚本
src/final-animation/       最终主线动画与后期合成代码
src/prototype-manimce/     早期 ManimCE 原型
tools/keyframe-editor/     相机与关键帧编辑工具
```

## 快速运行

先准备环境：

```bash
bash scripts/setup/setup-manimgl-env.sh
```

生成最终版的源视频：

```bash
bash scripts/render/render-final-source.sh
```

生成带矩形层的中间版：

```bash
bash scripts/render/render-final-overlay.sh
```

生成 canonical final：

```bash
bash scripts/render/render-final-video.sh
```

默认目标是：

- `1920x1080`
- `60fps`
- dark theme

如果你只是想看单帧 probe，可以用：

```bash
MANIM_CLIP_TIME=8.98 bash scripts/render/render-frame-probe.sh
```

## 研究内容概览

- `src/final-animation/`
  最终版主线，包括 revolve slice 场景、differential 插入段和矩形后期合成器。
- `src/prototype-manimce/`
  早期的 ManimCE 版本，用来验证动画结构和精确 clip 行为。
- `tools/keyframe-editor/`
  用于调相机、标签和关键帧的编辑器。
- `scripts/analysis/`
  CPU / GPU 对比、批量渲染和稳定性检查脚本。

补充说明见：

- [`docs/overview.md`](docs/overview.md)
- [`docs/research-notes.md`](docs/research-notes.md)

## 说明与致谢

- 这个仓库公开的是过程与结果，不包含本地渲染缓存、中间帧和虚拟环境。
- 环境依赖基于 `manimgl 1.7.2`，并通过 `scripts/setup/setup-manimgl-env.sh` 复现本地兼容补丁。
- 项目在工作流上参考了 `3b1b/manimgl` 生态的思路，但这里保留的是本仓库自己的场景组织与后期流程。
