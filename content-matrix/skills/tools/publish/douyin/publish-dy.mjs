#!/usr/bin/env node
/**
 * 抖音自动发布脚本（独立版）
 *
 * 功能：
 *   - 自动上传视频到抖音创作者平台
 *   - 自动填写描述/标题
 *   - 持久化浏览器登录态，免重复扫码
 *
 * 用法：
 *   node publish-dy.mjs --video=/path/to/video.mp4
 *   node publish-dy.mjs --video=./video.mp4 --desc="#话题 描述" --title="视频标题"
 *
 * 参数：
 *   --video=<路径>    视频文件路径（必填）
 *   --desc=<描述>     视频描述文字（可选）
 *   --title=<标题>    视频标题（可选）
 */

import 'dotenv/config';
import { Stagehand } from '@browserbasehq/stagehand';
import { existsSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { homedir } from 'os';

// ─── 路径工具 ───
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ─── 参数解析 ───
const args = process.argv.slice(2);

function getArg(prefix) {
    const a = args.find(a => a.startsWith(prefix));
    return a ? a.slice(prefix.length) : null;
}

const videoRaw = getArg('--video=');
if (!videoRaw) {
    console.error('❌ 请指定视频文件路径：--video=/path/to/video.mp4');
    process.exit(1);
}
const videoPath = resolve(process.cwd(), videoRaw);
if (!existsSync(videoPath)) {
    console.error(`❌ 视频文件不存在：${videoPath}`);
    process.exit(1);
}

const videoDesc = getArg('--desc=') || '';
const videoTitle = getArg('--title=') || '';

// ─── LLM 配置 ───
function getModelConfig() {
    const hasAnthropic = !!process.env.ANTHROPIC_API_KEY;
    const hasOpenAI = !!process.env.OPENAI_API_KEY;

    if (!hasAnthropic && !hasOpenAI) {
        console.error('❌ 缺少 LLM API Key');
        console.error('   请在 .env 中配置：ANTHROPIC_API_KEY=sk-... 或 OPENAI_API_KEY=sk-...');
        process.exit(1);
    }

    const modelName = process.env.STAGEHAND_MODEL
        || (hasAnthropic ? 'anthropic/claude-haiku-4-5-20251001' : 'openai/gpt-4o');
    const baseURL = process.env.ANTHROPIC_BASE_URL || null;

    if (baseURL && hasAnthropic) {
        return {
            model: { modelName, apiKey: process.env.ANTHROPIC_API_KEY, baseURL },
            provider: `中转 (${new URL(baseURL).hostname})`,
        };
    }
    return {
        model: modelName,
        provider: hasAnthropic ? 'Anthropic' : 'OpenAI',
    };
}

const modelConfig = getModelConfig();

// ─── 浏览器登录态目录（固定在 ~/.douyin-publish/ 下，跨项目共享） ───
const DY_PUBLISH_URL = 'https://creator.douyin.com/creator-micro/content/upload';
const userDataDir = resolve(homedir(), '.douyin-publish/chrome-data');
if (!existsSync(userDataDir)) mkdirSync(userDataDir, { recursive: true });

// ─── 打印配置 ───
console.log(`\n🎬 抖音自动发布`);
console.log(`   视频：${videoPath}`);
console.log(`   描述：${videoDesc || '（无）'}`);
if (videoTitle) console.log(`   标题：${videoTitle}`);
console.log(`   LLM：${modelConfig.provider}`);
console.log('');

// ─── 工具函数 ───
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function waitForEnter(prompt) {
    if (prompt) console.log(prompt);
    return new Promise((resolve) => {
        process.stdin.setRawMode?.(false);
        process.stdin.resume();
        process.stdin.once('data', () => { process.stdin.pause(); resolve(); });
    });
}

// ─── 主流程 ───
async function main() {
    // ═══ Step 1：初始化浏览器 ═══
    console.log('📌 Step 1：初始化浏览器...');
    const stagehand = new Stagehand({
        env: 'LOCAL',
        localBrowserLaunchOptions: {
            headless: false,
            viewport: { width: 1380, height: 900 },
            userDataDir,
            preserveUserDataDir: true,
        },
        model: modelConfig.model,
    });
    await stagehand.init();
    console.log('   ✅ 浏览器已启动');
    const page = stagehand.context.pages()[0];

    try {
        // ═══ Step 2：打开抖音创作者发布页 ═══
        console.log('\n📌 Step 2：打开发布页...');
        await page.goto(DY_PUBLISH_URL, { waitUntil: 'domcontentloaded' });
        await sleep(5000);

        // 检查是否需要登录
        const currentUrl = page.url();
        if (currentUrl.includes('login') || currentUrl.includes('passport')) {
            console.log('📱 需要登录，请在 Chromium 浏览器中用抖音 App 扫码登录...');
            await waitForEnter('   登录完成后按回车继续...');
            await page.goto(DY_PUBLISH_URL, { waitUntil: 'domcontentloaded' });
            await sleep(5000);
        }
        console.log('   ✅ 发布页已打开');

        // ═══ Step 3：上传视频 ═══
        console.log('\n📌 Step 3：上传视频...');
        try {
            // 暴露隐藏的 file input
            await page.evaluate(() => {
                document.querySelectorAll('input[type="file"]').forEach(input => {
                    input.style.cssText = 'opacity:1!important;display:block!important;position:fixed!important;top:50px!important;left:50px!important;width:300px!important;height:100px!important;z-index:999999!important;';
                });
            });
            await sleep(1000);
            await page.locator('input[type="file"]').first().setInputFiles(videoPath);
            console.log('   ✅ 视频已上传');
        } catch (err) {
            console.log(`   ❌ 自动上传失败：${err.message.substring(0, 80)}`);
            await waitForEnter('   请在浏览器中手动上传视频后按回车...');
        }

        // 等待视频处理
        console.log('\n⏳ 等待视频处理...');
        let videoReady = false;
        for (let i = 0; i < 60; i++) {
            await sleep(5000);
            process.stdout.write(`\r   已等待 ${(i + 1) * 5} 秒...`);
            try {
                const ready = await page.evaluate(() => {
                    const btns = document.querySelectorAll('button');
                    for (const b of btns) {
                        if (b.textContent?.trim() === '发布' && !b.disabled) return true;
                    }
                    return false;
                });
                if (ready) { console.log('\n   ✅ 视频处理完成'); videoReady = true; break; }
            } catch { }
        }
        if (!videoReady) console.log('\n   ⚠️ 等待超时，尝试继续...');

        // ═══ Step 4：填写描述/标题 ═══
        console.log('\n📌 Step 4：填写视频信息...');

        if (videoDesc) {
            try {
                const filled = await page.evaluate((desc) => {
                    const selectors = [
                        '.notranslate[contenteditable="true"]',
                        '[contenteditable="true"]',
                        '.ql-editor',
                        '.DraftEditor-root [contenteditable="true"]',
                        'textarea',
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.offsetWidth > 0) {
                            el.focus();
                            if (el.tagName === 'TEXTAREA') {
                                el.value = desc;
                            } else {
                                el.innerHTML = desc;
                            }
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            return { ok: true };
                        }
                    }
                    return { ok: false };
                }, videoDesc);

                if (filled.ok) {
                    console.log('   ✅ 描述已填写');
                } else {
                    await stagehand.act(`在视频描述输入框中输入"${videoDesc}"`);
                    console.log('   ✅ 描述已填写（AI 辅助）');
                }
            } catch (err) {
                console.log(`   ⚠️ 描述填写失败：${err.message.substring(0, 60)}`);
            }
        } else {
            console.log('   跳过描述（未指定）');
        }

        if (videoTitle) {
            try {
                await stagehand.act(`在标题输入框中输入"${videoTitle}"`);
                console.log('   ✅ 标题已填写');
            } catch (err) {
                console.log(`   ⚠️ 标题填写失败：${err.message.substring(0, 60)}`);
            }
        }

        await sleep(2000);

        // ═══ Step 5：点击发布 ═══
        console.log('\n📌 Step 5：点击发布...');
        try {
            const published = await page.evaluate(() => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    if (b.textContent?.trim() === '发布' && !b.disabled) {
                        b.click();
                        return true;
                    }
                }
                return false;
            });
            if (published) {
                console.log('   ✅ 已点击发布');
            } else {
                await stagehand.act('点击"发布"按钮');
                console.log('   ✅ 已点击发布（AI 辅助）');
            }
        } catch (err) {
            console.log(`   ⚠️ ${err.message.substring(0, 80)}`);
        }

        // 等待页面跳转
        for (let i = 0; i < 15; i++) {
            await sleep(2000);
            if (!page.url().includes('/upload')) {
                console.log(`   ✅ 页面已跳转`);
                break;
            }
            try {
                const r = await page.evaluate(() => {
                    const btns = document.querySelectorAll('button');
                    for (const b of btns) {
                        const t = b.textContent?.trim();
                        if (['确认', '确定', '我知道了', '知道了'].includes(t) && !b.disabled && b.offsetParent !== null) {
                            b.click();
                            return t;
                        }
                    }
                    return null;
                });
                if (r) console.log(`   ✅ 已处理弹窗：「${r}」`);
            } catch { }
        }

        await sleep(3000);

        // ═══ 完成 ═══
        const afterUrl = page.url();
        if (!afterUrl.includes('/upload')) {
            console.log('\n🎉 发布成功！');
        } else {
            console.log('\n⚠️ 请在抖音创作者后台确认发布状态');
        }
        console.log('\n' + '═'.repeat(50));
        console.log('🎉 抖音发布流程完成！');
        console.log('═'.repeat(50));

    } catch (err) {
        console.error(`\n❌ 出错：${err.message}`);
        console.error(err.stack);
    }

    console.log('\n⏳ 5 秒后关闭浏览器...');
    await sleep(5000);
    await stagehand.close();
    console.log('🔚 浏览器已关闭');
}

main().catch((err) => {
    console.error('❌ 失败：', err.message);
    process.exit(1);
});
