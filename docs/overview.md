# Overview

## 这个仓库为什么同时有五块内容

`3DMath-lab` 不是单纯的成片仓，也不是只存实验脚本的草稿仓。
它把数学动画项目拆成五个公开层级：

- `src/final-animation/`
  圆盘切片与旋转体主片代码。
- `src/reference-animation/`
  `sqrt(x)` 绕 y 轴旋转参考片和参考帧的独立生产链。
- `web3d/`
  Steinmetz 两圆柱相交动画的 Three.js/Web3D 项目。
- `src/prototype-manimce/`
  早期实验和结构验证代码。
- `tools/keyframe-editor/`
  相机与标签编辑工具。

这样的组织方式有两个好处：

- 只想看结果的人可以快速定位到最终版。
- 想研究过程的人也能顺着原型、工具和批处理脚本追溯完整工作流。

## 如果你只想看结果

优先看这四个位置：

- [`../assets/final/volume-of-revolution/`](../assets/final/volume-of-revolution/)
- [`../assets/final/sqrtx-y-rotation/`](../assets/final/sqrtx-y-rotation/)
- [`../assets/final/steinmetz-intersection/`](../assets/final/steinmetz-intersection/)
- [`../README.md`](../README.md)

如果你想看每个作品的整理说明，再看：

- [`works/volume-of-revolution.md`](works/volume-of-revolution.md)
- [`works/sqrtx-y-rotation.md`](works/sqrtx-y-rotation.md)
- [`works/steinmetz-intersection.md`](works/steinmetz-intersection.md)

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

### `web3d/`

- `src/main.js`
  Steinmetz 两圆柱相交动画主逻辑。
- `scripts/capture.mjs`
  用 Playwright 捕获关键帧，并通过 ffmpeg 合成 `1080p60` 视频。

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
- `web3d/node_modules/`
- `.venv/`
- `.venv-manimgl/`
- 中间帧、probe、contact sheet
- 临时试片和缓存资源

这样仓库首页保持干净，真正的大体积生成物留给本地或 Release 附件处理。
