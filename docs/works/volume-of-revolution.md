# 圆盘切片与旋转体

## 成品

- 视频：[`../../assets/final/volume-of-revolution/volume-of-revolution-1080p60.mp4`](../../assets/final/volume-of-revolution/volume-of-revolution-1080p60.mp4)
- 封面：[`../../assets/final/volume-of-revolution/cover.png`](../../assets/final/volume-of-revolution/cover.png)
- 终帧：[`../../assets/final/volume-of-revolution/final-frame.png`](../../assets/final/volume-of-revolution/final-frame.png)

规格：

- `1920x1080`
- `60fps`
- `22.1s`
- 黑色背景，freeze-end 收尾

## 内容

这条主片展示从二维面积微元出发，通过代表性矩形、圆盘切片和后续批量旋转，建立旋转体体积的直观图像。

## 源码与生成链路

核心源码：

- [`../../src/final-animation/revolve-slice-core.py`](../../src/final-animation/revolve-slice-core.py)
- [`../../src/final-animation/revolve-slice-differential.py`](../../src/final-animation/revolve-slice-differential.py)
- [`../../src/final-animation/rectangle-overlay-compositor.py`](../../src/final-animation/rectangle-overlay-compositor.py)

渲染入口：

- [`../../scripts/render/render-final-source.sh`](../../scripts/render/render-final-source.sh)
- [`../../scripts/render/render-final-overlay.sh`](../../scripts/render/render-final-overlay.sh)
- [`../../scripts/render/render-final-video.sh`](../../scripts/render/render-final-video.sh)

更完整的生产链路见 [`../final-pipeline.md`](../final-pipeline.md)。
