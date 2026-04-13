# Overview

## 这个仓库为什么同时有四块内容

`3DMath-lab` 不是单纯的成片仓，也不是只存实验脚本的草稿仓。
它把同一条动画项目拆成四个公开层级：

- `src/final-animation/`
  真正负责最终版成片的代码。
- `src/reference-animation/`
  固定机位参考片和参考帧的独立生产链。
- `src/prototype-manimce/`
  早期实验和结构验证代码。
- `tools/keyframe-editor/`
  相机与标签编辑工具。

这样的组织方式有两个好处：

- 只想看结果的人可以快速定位到最终版。
- 想研究过程的人也能顺着原型、工具和批处理脚本追溯完整工作流。

## 如果你只想看结果

优先看这三个位置：

- [`../assets/final/volume-of-revolution-final-1080p60.mp4`](../assets/final/volume-of-revolution-final-1080p60.mp4)
- [`../README.md`](../README.md)
- [`final-pipeline.md`](final-pipeline.md)

如果你想看这次为了 `sqrt(x)` 固定机位参考视频到底新增了什么，再看：

- [`reference-video-upgrade.md`](reference-video-upgrade.md)

## 代码分区说明

### `src/final-animation/`

- `revolve-slice-core.py`
  最基础的 revolve slice 场景。
- `revolve-slice-differential.py`
  在 hero disk 之后插入 differential 说明段的最终主场景。
- `rectangle-overlay-compositor.py`
  把 linked rectangles 合成到既有渲染上的后期脚本。
- `minimal-smoke-scene.py`
  环境 smoke test。

### `src/reference-animation/`

- `sqrtx_full_rotation.py`
  `sqrt(x)` 固定机位参考视频与参考帧场景。

### `src/prototype-manimce/`

- `revolve-slice-prototype.py`
  早期 ManimCE 原型。
- `make-contact-sheet.py`
  原型渲染后的联系图拼接脚本。

### `tools/keyframe-editor/`

- `editor-server.py`
  本地编辑器服务。
- `label-editor.html`
  标签关键帧编辑页面。
- `camera-editor.html`
  相机关键帧编辑页面。
- `reference-label-editor.html`
  参考视频 `xyz` 标签布局编辑页面。
- `reference-camera-editor.html`
  参考视频固定机位与参考帧编辑页面。

### `scripts/`

- `setup/`
  环境准备与兼容补丁。
- `render/`
  最终主链路和原型渲染入口。
- `analysis/`
  稳定性、CPU/GPU 对比和批量工具。
- `windows/`
  Windows 机器上的辅助入口。

## 本次参考视频升级的入口

如果你想从“新增了什么”这个角度看仓库，建议按这个顺序：

1. [`reference-video-upgrade.md`](reference-video-upgrade.md)
2. [`../src/reference-animation/sqrtx_full_rotation.py`](../src/reference-animation/sqrtx_full_rotation.py)
3. [`../scripts/render/render-sqrtx-reference.sh`](../scripts/render/render-sqrtx-reference.sh)
4. [`../tools/keyframe-editor/reference-camera-editor.html`](../tools/keyframe-editor/reference-camera-editor.html)
5. [`../tools/keyframe-editor/reference-label-editor.html`](../tools/keyframe-editor/reference-label-editor.html)

## 公开仓不包含什么

以下内容默认不入库：

- `output/`
- `media/`
- `.venv/`
- `.venv-manimgl/`
- 中间帧、probe、contact sheet
- 临时试片和缓存资源

这样仓库首页保持干净，真正的大体积生成物留给本地或 Release 附件处理。
