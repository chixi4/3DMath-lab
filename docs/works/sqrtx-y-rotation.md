# `sqrt(x)` 绕 y 轴旋转参考片

## 成品

- Phi 30 视频：[`../../assets/final/sqrtx-y-rotation/sqrtx-y-rotation-phi30-4k60.mp4`](../../assets/final/sqrtx-y-rotation/sqrtx-y-rotation-phi30-4k60.mp4)
- Phi 70 视频：[`../../assets/final/sqrtx-y-rotation/sqrtx-y-rotation-phi70-4k60.mp4`](../../assets/final/sqrtx-y-rotation/sqrtx-y-rotation-phi70-4k60.mp4)
- Phi 30 封面：[`../../assets/final/sqrtx-y-rotation/cover-phi30.png`](../../assets/final/sqrtx-y-rotation/cover-phi30.png)
- Phi 70 封面：[`../../assets/final/sqrtx-y-rotation/cover-phi70.png`](../../assets/final/sqrtx-y-rotation/cover-phi70.png)

规格：

- `3840x2160`
- `60fps`
- `7.6s`
- 黑色背景
- `phi30 / phi70` 两个固定机位版本

## 内容

这组参考片展示 `sqrt(x)` 平面区域绕 y 轴旋转，逐步形成完整旋转体。它和圆盘切片主片不同：这里的重点是完整对象绕 y 轴的参考展示，以及固定机位下的清晰标签和网格。

## 源码与生成链路

核心源码：

- [`../../src/reference-animation/sqrtx_full_rotation.py`](../../src/reference-animation/sqrtx_full_rotation.py)
- [`../../scripts/render/composite-sqrtx-reference-labels.py`](../../scripts/render/composite-sqrtx-reference-labels.py)
- [`../../config/reference-label-layouts.json`](../../config/reference-label-layouts.json)

渲染入口：

- [`../../scripts/render/render-sqrtx-reference.sh`](../../scripts/render/render-sqrtx-reference.sh)

参考片升级说明见 [`../reference-video-upgrade.md`](../reference-video-upgrade.md)。
