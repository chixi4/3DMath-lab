import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(webRoot, "..");
const outputRoot = path.join(repoRoot, "output", "steinmetz-web3d");
const port = Number(process.env.PORT || 5174);
const baseUrl = `http://127.0.0.1:${port}`;
const duration = 34.0;
const fps = Number(process.env.FPS || 60);
const width = Number(process.env.WIDTH || 1920);
const height = Number(process.env.HEIGHT || 1080);

const keyframes = [
  ["01-axes", 0.6],
  ["02-first-quarter-cylinder", 2.4],
  ["03-second-quarter-cylinder", 4.55],
  ["04-both-quarter-cylinders", 5.75],
  ["05-fade-remnants", 7.35],
  ["06-tent-isolated", 9.35],
  ["06b-formulas-held", 11.1],
  ["07-final", 17.2],
  ["08-return-single-block", 20.75],
  ["08b-return-finished", 23.10],
  ["08c-growing-full-cylinders", 24.35],
  ["09-eight-octants-single-fades", 25.70],
  ["10-blue-front", 26.48],
  ["10-blue-back", 27.06],
  ["10-pink-front", 27.64],
  ["10-pink-back", 28.22],
  ["10-orange-front", 28.80],
  ["10-orange-back", 29.38],
  ["10-green-front", 29.96],
  ["10-green-back", 30.54],
  ["11-symmetry-final", 32.55],
];

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      stdio: "inherit",
      ...options,
    });
    child.on("exit", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${command} exited with ${code}`));
    });
    child.on("error", reject);
  });
}

async function waitForServer(url, timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Keep waiting while Vite starts.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function startServer() {
  const npm = process.platform === "win32" ? "npm.cmd" : "npm";
  const child = spawn(npm, ["run", "dev", "--", "--port", String(port), "--strictPort"], {
    cwd: webRoot,
    stdio: ["ignore", "pipe", "pipe"],
  });
  child.stdout.on("data", (chunk) => process.stdout.write(chunk));
  child.stderr.on("data", (chunk) => process.stderr.write(chunk));
  await waitForServer(baseUrl);
  return child;
}

async function openPage() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  await page.goto(`${baseUrl}/?capture=1&t=0`, { waitUntil: "networkidle" });
  await page.waitForFunction(() => window.__steinmetzReady === true);
  return { browser, page };
}

async function captureAt(page, label, time, directory) {
  const stats = await page.evaluate((value) => window.steinmetzSetTime(value), time);
  if (stats.nonDarkRatio < 0.002) {
    throw new Error(`${label} looks blank: ${JSON.stringify(stats)}`);
  }
  const file = path.join(directory, `${label}.png`);
  await page.screenshot({ path: file, fullPage: false });
  return { label, time, file, stats };
}

async function captureKeyframes(page) {
  const directory = path.join(outputRoot, "keyframes");
  await mkdir(directory, { recursive: true });
  const results = [];
  for (const [label, time] of keyframes) {
    const result = await captureAt(page, label, time, directory);
    results.push(result);
    console.log(`${label} t=${time.toFixed(2)} nonDark=${result.stats.nonDarkRatio.toFixed(4)} saturated=${result.stats.saturatedRatio.toFixed(4)}`);
  }
  await writeFile(path.join(directory, "stats.json"), JSON.stringify(results, null, 2));
  return results;
}

async function captureVideo(page) {
  const framesDir = path.join(outputRoot, "frames");
  await rm(framesDir, { recursive: true, force: true });
  await mkdir(framesDir, { recursive: true });
  const totalFrames = Math.round(duration * fps);
  for (let frame = 0; frame < totalFrames; frame += 1) {
    const time = frame / fps;
    await page.evaluate((value) => window.steinmetzSetTime(value), time);
    await page.screenshot({
      path: path.join(framesDir, `frame_${String(frame).padStart(5, "0")}.png`),
      fullPage: false,
    });
    if (frame % Math.max(1, Math.round(fps)) === 0) {
      console.log(`frame ${frame}/${totalFrames}`);
    }
  }
  const videoPath = path.join(outputRoot, "steinmetz-web3d-1080p60.mp4");
  await run("ffmpeg", [
    "-hide_banner",
    "-loglevel",
    "error",
    "-y",
    "-framerate",
    String(fps),
    "-i",
    path.join(framesDir, "frame_%05d.png"),
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-crf",
    "17",
    "-preset",
    "slow",
    videoPath,
  ]);
  console.log(`video ready: ${videoPath}`);
  return videoPath;
}

async function main() {
  const mode = process.argv[2] || "keyframes";
  await mkdir(outputRoot, { recursive: true });
  const server = await startServer();
  let browser;
  try {
    const opened = await openPage();
    browser = opened.browser;
    if (mode === "video") {
      await captureKeyframes(opened.page);
      await captureVideo(opened.page);
    } else {
      await captureKeyframes(opened.page);
    }
  } finally {
    if (browser) await browser.close();
    server.kill("SIGTERM");
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
