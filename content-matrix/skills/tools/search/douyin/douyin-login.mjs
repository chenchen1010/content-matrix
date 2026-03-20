#!/usr/bin/env node
/**
 * 抖音登录助手 — 登录成功后自动保存 Cookie 并关闭浏览器
 *
 * - 合并 Playwright 内所有 douyin 相关 Cookie（不仅限 www 单域）
 * - User-Agent 与 douyin_mcp 客户端一致（Chrome 135），减少签名校验偏差
 * - login_probe：history/read 失败时尝试「搜索是否有结果」作为备用成功条件
 * - DOM 备用：轮询多次 API 仍失败但页面明显已登录时，仍保存 Cookie 并提示用搜索自检
 * - 显式 process.exit(0)，避免子进程挂起导致终端不结束
 */

import { chromium } from "playwright";
import { writeFileSync, unlinkSync, existsSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { spawnSync } from "child_process";
import { tmpdir } from "os";
import { randomBytes } from "crypto";

const __dirname = dirname(fileURLToPath(import.meta.url));
const COOKIES_PATH = join(__dirname, "douyin_mcp", "cookies.txt");
const DOUYIN_URL = "https://www.douyin.com";
const DOUYIN_MCP_DIR = join(__dirname, "douyin_mcp");
/** 与 src/token_manager.py DOUYIN_FIXED_USER_AGENT 一致 */
const PLAYWRIGHT_UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36";

const POLL_MS = 3000;
const MAX_WAIT_MS = 10 * 60 * 1000;
const DOM_FALLBACK_AFTER_MS = 45 * 1000; // 45s 后若页面像已登录，仍保存并退出

function formatCookiesFromPlaywright(cookies) {
  const douyin = cookies.filter(
    (c) =>
      (c.domain && (c.domain.includes("douyin") || c.domain.includes("iesdouyin"))) ||
      (c.name && /douyin|ttwid|sessionid|passport|sid_guard/i.test(c.name))
  );
  if (douyin.length === 0) {
    return cookies.map((c) => `${c.name}=${c.value}`).join("; ");
  }
  const byName = new Map();
  for (const c of douyin) {
    byName.set(c.name, c.value);
  }
  return Array.from(byName.entries())
    .map(([n, v]) => `${n}=${v}`)
    .join("; ");
}

function probeLoginWithMcp(cookieStr) {
  const probeFile = join(
    tmpdir(),
    `douyin-cookie-probe-${randomBytes(8).toString("hex")}.txt`
  );
  writeFileSync(probeFile, cookieStr, "utf8");

  const env = {
    ...process.env,
    DOUYIN_COOKIE_FILE: probeFile,
    PYTHONUNBUFFERED: "1",
  };

  let r = spawnSync("uv", ["run", "python", "login_probe.py"], {
    cwd: DOUYIN_MCP_DIR,
    env,
    encoding: "utf-8",
    timeout: 60000,
  });

  let out = (r.stdout || "").trim().split(/\r?\n/).pop() || "";
  if (out !== "true" && out !== "false") {
    const py = join(DOUYIN_MCP_DIR, ".venv", "bin", "python3");
    if (existsSync(py)) {
      r = spawnSync(py, [join(DOUYIN_MCP_DIR, "login_probe.py")], {
        cwd: DOUYIN_MCP_DIR,
        env,
        encoding: "utf-8",
        timeout: 60000,
      });
      out = (r.stdout || "").trim().split(/\r?\n/).pop() || "";
    }
  }

  try {
    unlinkSync(probeFile);
  } catch {
    /* ignore */
  }

  return out === "true";
}

async function domLooksLoggedIn(page) {
  try {
    return await page.evaluate(() => !!document.querySelector('a[href*="/user/self"]'));
  } catch {
    return false;
  }
}

async function main() {
  console.log("");
  console.log("🌐 正在打开浏览器…");
  console.log("");
  console.log("   请在窗口内完成抖音登录。检测到会话可用后会自动保存 Cookie 并关闭浏览器。");
  console.log("");

  const browser = await chromium
    .launch({
      headless: false,
      channel: "chrome",
    })
    .catch(() => chromium.launch({ headless: false }));

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    userAgent: PLAYWRIGHT_UA,
  });

  const page = await context.newPage();
  await page.goto(DOUYIN_URL, { waitUntil: "domcontentloaded" });

  const start = Date.now();
  let saved = false;
  let domFallbackUsed = false;

  try {
    while (Date.now() - start < MAX_WAIT_MS) {
      await new Promise((resolve) => setTimeout(resolve, POLL_MS));

      const allCookies = await context.cookies();
      if (allCookies.length === 0) {
        process.stdout.write(".");
        continue;
      }

      const cookieStr = formatCookiesFromPlaywright(allCookies);

      try {
        if (probeLoginWithMcp(cookieStr)) {
          writeFileSync(COOKIES_PATH, cookieStr, "utf8");
          console.log("");
          console.log("✅ 已检测到会话可用（接口校验通过）");
          console.log("✅ Cookie 已保存:", COOKIES_PATH);
          saved = true;
          break;
        }
      } catch {
        /* continue */
      }

      const elapsed = Date.now() - start;
      if (elapsed >= DOM_FALLBACK_AFTER_MS && (await domLooksLoggedIn(page))) {
        writeFileSync(COOKIES_PATH, cookieStr, "utf8");
        console.log("");
        console.log("⚠️ 接口校验未通过，但页面疑似已登录，已保存当前 Cookie。");
        console.log("   请在本机执行：mcporter call 'douyin_search.search_videos(keyword: \"夜校\", count: 3)'");
        console.log("   若仍为空，请重新运行本登录脚本。");
        console.log("✅ Cookie 已保存:", COOKIES_PATH);
        domFallbackUsed = true;
        saved = true;
        break;
      }

      process.stdout.write(".");
    }

    if (!saved) {
      console.log("");
      console.log("⏱️ 超时（10 分钟）。可重新运行本脚本。");
    }
  } finally {
    await browser.close().catch(() => {});
    console.log("✅ 浏览器已关闭。");
    console.log("");
  }

  process.exit(0);
}

main().catch((e) => {
  console.error("❌ 错误:", e.message);
  process.exit(1);
});
