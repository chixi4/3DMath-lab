# Reference Video Upgrade

## 这份整理文档是在回答什么

这次为了交付最新的 `sqrt(x)` 参考视频，仓库相比原始项目并不是只多了两个输出文件，而是补齐了一整条新的“固定机位参考视频”生产链。

和原项目相比，新增内容可以归成五组：

1. 独立的 `sqrt(x)` 参考场景与渲染入口
2. 参考视频专用的 2D `x / y / z` 叠字链路
3. 可视化编辑工具：参考相机编辑器 + 标签布局编辑器
4. 为固定机位复用而补到最终动画主链路里的底层开关
5. 参考视频专用配置，以及运行时自动生成的纹理/标签资产

## 1. 新增了独立的参考动画代码区

新增：

- [`../src/reference-animation/sqrtx_full_rotation.py`](../src/reference-animation/sqrtx_full_rotation.py)
- [`../scripts/render/render-sqrtx-reference.sh`](../scripts/render/render-sqrtx-reference.sh)

这部分把参考视频从原来的最终动画主线里拆了出来，形成了一条单独可渲染、可维护的 scene。

它现在额外承担了这些职责：

- 固定机位参考视角参数
- `sqrt(x)` 旋转体的独立构造
- 逐帧 rebuild 的稳定视频输出路径
- 顶面/侧壁网格纹理生成
- 白色网格层与半透明实体层分离
- 参考帧预览用的静帧渲染入口

也就是说，最新视频不再是“从原场景里临时拼出来的一次性结果”，而是有了自己的 scene 和 render script。

## 2. 新增了参考视频专用的标签合成链路

新增：

- [`../scripts/render/composite-sqrtx-reference-labels.py`](../scripts/render/composite-sqrtx-reference-labels.py)
- [`../config/reference-label-layouts.json`](../config/reference-label-layouts.json)

这条链路把 `xyz` 从 3D 场景内部标签，改成了后期 2D overlay：

- 视频先输出无标签的基础版
- 再根据固定机位把 `x / y / z` 投到屏幕空间
- 最终按 JSON 布局把纯白字体叠到成片上

这样新增了两个很关键的能力：

- 标签位置不再写死在 3D 场景里，可以独立迭代
- 最终标签布局可以由 GUI 人工确认，而不是靠脚本猜位置

目前这份 JSON 已经保存了最新成片使用的 `phi30 / phi70` 坐标。

## 3. 新增了两类可视化编辑器

新增：

- [`../tools/keyframe-editor/reference-camera-editor.html`](../tools/keyframe-editor/reference-camera-editor.html)
- [`../tools/keyframe-editor/reference-label-editor.html`](../tools/keyframe-editor/reference-label-editor.html)

扩展：

- [`../tools/keyframe-editor/editor-server.py`](../tools/keyframe-editor/editor-server.py)

和原项目只支持原型标签/相机编辑相比，现在编辑器服务额外支持：

- 读取和回写 `sqrt(x)` 参考场景里的固定机位参数
- 本地触发参考帧静态预览渲染
- 管理 `phi30 / phi70` 两套标签布局
- 在 4K 背景图上直接拖拽 `xyz` 位置并保存

也就是说，仓库现在多了一套专门为参考视频服务的本地 GUI 工作流，而不是只能手改 Python 常量。

## 4. 为固定机位输出补了底层兼容开关

调整：

- [`../src/final-animation/revolve-slice-core.py`](../src/final-animation/revolve-slice-core.py)
- [`../src/final-animation/revolve-slice-differential.py`](../src/final-animation/revolve-slice-differential.py)
- [`../src/final-animation/rectangle-overlay-compositor.py`](../src/final-animation/rectangle-overlay-compositor.py)
- [`../scripts/render/render-final-source.sh`](../scripts/render/render-final-source.sh)
- [`../scripts/render/render-final-overlay.sh`](../scripts/render/render-final-overlay.sh)
- [`../scripts/render/render-final-fixed-camera.sh`](../scripts/render/render-final-fixed-camera.sh)

这些改动不是在直接生成 `sqrt(x)` 参考视频本身，但它们是本次需求带出来的基础设施整理：

- 最终动画主场景新增 `fixed/static/locked` 相机模式
- linked-rectangles 后期脚本支持固定相机投影
- fixed-camera 模式下的矩形 build emphasis 可调
- 渲染脚本对本地虚拟环境路径更宽容
- 新增固定机位版本的一键脚本入口

这部分让“固定机位”从一次性的本地实验，变成了主链路也能理解的正式能力。

## 5. 增加了参考视频的专用资产机制

运行时会自动生成：

- `assets/reference-textures/`
- `assets/reference-labels/`

这些资产包括：

- 顶面/侧壁的 fill texture
- 透明底白色网格 texture
- `x / y / z` 的 SVG/PNG 纹理资产

它们现在由代码自动生成，不作为源码人工维护，所以已经通过 [`.gitignore`](../.gitignore) 从版本控制里排除了。相比原项目，这代表仓库新增了一类“源码驱动的中间资产”，但我们把它整理成了：

- 代码负责生成
- Git 不跟踪运行时产物
- 仓库只保留真正需要维护的脚本和配置

## 文件级总览

### 新增源码 / 配置

- `src/reference-animation/sqrtx_full_rotation.py`
- `scripts/render/render-sqrtx-reference.sh`
- `scripts/render/composite-sqrtx-reference-labels.py`
- `scripts/render/render-final-fixed-camera.sh`
- `tools/keyframe-editor/reference-camera-editor.html`
- `tools/keyframe-editor/reference-label-editor.html`
- `config/reference-label-layouts.json`

### 扩展的既有源码

- `tools/keyframe-editor/editor-server.py`
- `src/final-animation/revolve-slice-core.py`
- `src/final-animation/revolve-slice-differential.py`
- `src/final-animation/rectangle-overlay-compositor.py`
- `scripts/render/render-final-source.sh`
- `scripts/render/render-final-overlay.sh`

### 新增但不入库的运行时资产

- `assets/reference-textures/*`
- `assets/reference-labels/*`

## 现在仓库多出来的核心能力

最终可以把这次升级理解成：仓库从“只有最终主片生产链”，变成了同时具备下面两条正式链路：

- 最终主片链路：`final-animation`
- 固定机位参考片链路：`reference-animation`

并且参考片链路不是黑盒：

- 有独立 scene
- 有独立 render script
- 有 GUI 调相机
- 有 GUI 调标签
- 有可提交的标签布局配置
- 有稳定的 4K60 输出路径

这就是这次相对原项目真正增加的东西。
