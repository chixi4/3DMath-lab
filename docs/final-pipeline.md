# Final Pipeline

## Canonical final

当前唯一正式版本是：

- [`../assets/final/volume-of-revolution-final-1080p60.mp4`](../assets/final/volume-of-revolution-final-1080p60.mp4)

它对应的是黑底、`1080p / 60fps`、freeze-end 收尾版本。

## 三步生成链路

### 1. Source render

入口：

- [`../scripts/render/render-final-source.sh`](../scripts/render/render-final-source.sh)

职责：

- 运行 `RevolveSliceShowcaseMGLDifferential`
- 输出带 differential 节奏的源视频
- 保留最终版相机与 hero disk 节奏

默认输出：

- `output/final/volume-of-revolution-source-1080p60.mp4`

### 2. Rectangle overlay

入口：

- [`../scripts/render/render-final-overlay.sh`](../scripts/render/render-final-overlay.sh)

职责：

- 读取 source render
- 叠加 linked rectangles 平面矩形层
- 输出最终收尾前的 overlay 版本

默认输出：

- `output/final/volume-of-revolution-overlay-1080p60.mp4`

### 3. Freeze ending

入口：

- [`../scripts/render/render-final-video.sh`](../scripts/render/render-final-video.sh)

职责：

- 在视角稳定后冻结一帧
- 淡到只保留矩形的终态帧
- 保持最后一秒定格

默认输出：

- `output/final/volume-of-revolution-final-1080p60.mp4`

## 为什么 freeze-end 是 canonical final

这个版本解决了前一版结尾里“整体体积渐隐不够稳定”的问题。
最终镜头的处理不是重新渲染体积消失，而是基于稳定视角的后期拼接：

- 先停住
- 再切到仅保留矩形的终态
- 最后留出干净的结束画面

这样收尾更克制，也更适合作为最终提交版本。

## 相关代码位置

- [`../src/final-animation/revolve-slice-differential.py`](../src/final-animation/revolve-slice-differential.py)
- [`../src/final-animation/rectangle-overlay-compositor.py`](../src/final-animation/rectangle-overlay-compositor.py)
