# Steinmetz 两圆柱相交

## 成品

- 视频：[`../../assets/final/steinmetz-intersection/steinmetz-intersection-web3d-1080p60.mp4`](../../assets/final/steinmetz-intersection/steinmetz-intersection-web3d-1080p60.mp4)
- 封面：[`../../assets/final/steinmetz-intersection/cover.png`](../../assets/final/steinmetz-intersection/cover.png)
- 精选关键帧：[`../../assets/final/steinmetz-intersection/keyframes/`](../../assets/final/steinmetz-intersection/keyframes/)

规格：

- `1920x1080`
- `60fps`
- `34.0s`
- Three.js/Web3D 渲染

## 内容

这条动画展示两个互相垂直的圆柱相交形成的 Steinmetz solid。叙事顺序包括：

1. 坐标轴与第一卦限空间
2. 两个四分之一圆柱的生成
3. 第一卦限内的单个“帐篷块”
4. 俯视积分公式
5. 完整正负半轴圆柱生成
6. 八个对称块依次高亮
7. 用对称性解释为什么第一卦限体积乘 8 得到整体体积

## 源码与生成链路

核心源码：

- [`../../web3d/src/main.js`](../../web3d/src/main.js)
- [`../../web3d/src/style.css`](../../web3d/src/style.css)
- [`../../web3d/scripts/capture.mjs`](../../web3d/scripts/capture.mjs)

本地运行：

```bash
cd web3d
npm install
npm run dev
```

渲染视频与关键帧：

```bash
cd web3d
npm run capture:video
```
