#!/usr/bin/env node
/**
 * 微信视频号自动发布脚本
 *
 * 功能：
 *   - 自动上传视频到微信视频号
 *   - 自动填写描述
 *   - 可选声明原创（勾选协议 + 确认）
 *   - 持久化浏览器登录态，免重复扫码
 *
 * 技术要点：
 *   - 微信视频号后台使用 wujie 微前端，DOM 在 iframe[name="content"] 中
 *   - Ant Design checkbox 需要点击 label.ant-checkbox-wrapper
 *   - 声明原创是两步流程：弹窗勾选 → 回到表单 → 需要再次点击发表
 *
 * 用法：
 *   node publish-sph.mjs --video=/path/to/video.mp4
 *   node publish-sph.mjs --video=./video.mp4 --desc="#话题 描述" --original
 *   node publish-sph.mjs --video=./video.mp4 --no-original
 *
 * 参数：
 *   --video=<路径>    视频文件路径（必填）
 *   --desc=<描述>     视频描述文字（可选）
 *   --original        声明原创（默认）
 *   --no-original     不声明原创，直接发表
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
const declareOriginal = !args.includes('--no-original');

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

// ─── 浏览器登录态目录（固定在 ~/.wechat-channels-publish/ 下，跨项目共享） ───
const SPH_PUBLISH_URL = 'https://channels.weixin.qq.com/platform/post/create';
const userDataDir = resolve(homedir(), '.wechat-channels-publish/chrome-data');
if (!existsSync(userDataDir)) mkdirSync(userDataDir, { recursive: true });

// ─── 打印配置 ───
console.log(`\n🎬 微信视频号自动发布`);
console.log(`   视频：${videoPath}`);
console.log(`   描述：${videoDesc || '（无）'}`);
console.log(`   原创：${declareOriginal ? '✅ 声明原创' : '❌ 不声明'}`);
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

/** 在 wujie iframe[name="content"] 中执行代码 */
async function execInWujie(page, fnBody, ...fnArgs) {
    return await page.evaluate(({ body, args }) => {
        const iframe = document.querySelector('iframe[name="content"]');
        if (!iframe) throw new Error('未找到 iframe[name="content"]');
        const doc = iframe.contentDocument || iframe.contentWindow?.document;
        if (!doc) throw new Error('无法访问 iframe document');
        const fn = new Function('doc', ...args.map((_, i) => `a${i}`), body);
        return fn(doc, ...args);
    }, { body: fnBody, args: fnArgs });
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
        // ═══ Step 2：打开视频号发布页 ═══
        console.log('\n📌 Step 2：打开发布页...');
        await page.goto(SPH_PUBLISH_URL, { waitUntil: 'domcontentloaded' });
        await sleep(5000);

        // 检查是否需要登录
        if (page.url().includes('login')) {
            console.log('📱 需要登录，请在 Chromium 浏览器中扫码登录微信视频号后台...');
            await waitForEnter('   登录完成后按回车继续...');
            await page.goto(SPH_PUBLISH_URL, { waitUntil: 'domcontentloaded' });
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
            await page.locator('input[type="file"]').setInputFiles(videoPath);
            console.log('   ✅ 视频已上传');
        } catch (err) {
            console.log(`   ❌ 自动上传失败：${err.message.substring(0, 80)}`);
            await waitForEnter('   请在浏览器中手动上传视频后按回车...');
        }

        // 等待视频处理完成
        console.log('\n⏳ 等待视频处理...');
        let videoReady = false;
        for (let i = 0; i < 60; i++) {
            await sleep(5000);
            process.stdout.write(`\r   已等待 ${(i + 1) * 5} 秒...`);
            try {
                const ready = await execInWujie(page, `
                    for (const b of doc.querySelectorAll('button'))
                        if (b.textContent?.trim() === '发表')
                            return !b.disabled && !b.classList.contains('weui-desktop-btn_disabled');
                    return false;
                `);
                if (ready) { console.log('\n   ✅ 视频处理完成'); videoReady = true; break; }
            } catch { }
        }
        if (!videoReady) {
            console.log('\n   ⚠️ 等待超时，尝试继续...');
        }

        // ═══ Step 4：填写描述 ═══
        if (videoDesc) {
            console.log('\n📌 Step 4：填写描述...');
            try {
                const fillResult = await execInWujie(page, `
                    const editor = doc.querySelector('.input-editor') || doc.querySelector('[contenteditable="true"]');
                    if (!editor) return { ok: false, err: '未找到编辑器' };
                    editor.focus();
                    editor.innerHTML = '<p>' + a0 + '</p>';
                    editor.dispatchEvent(new Event('input', { bubbles: true }));
                    return { ok: true, text: editor.textContent?.substring(0, 60) };
                `, videoDesc);
                console.log(fillResult.ok ? `   ✅ 描述：${fillResult.text}` : `   ⚠️ ${fillResult.err}`);
            } catch (err) {
                console.log(`   ⚠️ ${err.message.substring(0, 80)}`);
            }
        } else {
            console.log('\n📌 Step 4：跳过描述（未指定）');
        }

        await sleep(2000);

        // ═══ Step 5：点击发表 ═══
        console.log('\n📌 Step 5：点击发表...');
        await execInWujie(page, `
            for (const b of doc.querySelectorAll('button'))
                if (b.textContent?.trim() === '发表' && !b.disabled && !b.classList.contains('weui-desktop-btn_disabled'))
                    { b.click(); return true; }
            return false;
        `);
        console.log('   ✅ 已点击发表');
        await sleep(3000);

        // ═══ Step 6：处理弹窗 ═══
        if (declareOriginal) {
            // ─── 声明原创流程 ───
            console.log('\n📌 Step 6：声明原创...');

            // 6a: 弹窗1 → 点击"声明原创"
            console.log('   6a: 选择声明原创...');
            try {
                const r1 = await execInWujie(page, `
                    for (const wrp of doc.querySelectorAll('.weui-desktop-dialog__wrp')) {
                        if (wrp.offsetWidth === 0 && wrp.offsetHeight === 0) continue;
                        for (const b of wrp.querySelectorAll('button')) {
                            if (b.textContent?.trim() === '声明原创' && !b.disabled && !b.classList.contains('weui-desktop-btn_disabled')) {
                                b.click();
                                return { ok: true };
                            }
                        }
                    }
                    return { ok: false };
                `);
                console.log(r1.ok ? '   ✅ 已选择「声明原创」' : '   ⚠️ 未找到按钮');
            } catch (err) {
                console.log(`   ⚠️ ${err.message.substring(0, 80)}`);
            }

            await sleep(3000);

            // 6b: 弹窗2 → 勾选协议 → 点击确认
            console.log('   6b: 勾选协议并确认...');
            try {
                // 勾选 Ant Design checkbox
                const checkResult = await execInWujie(page, `
                    for (const wrp of doc.querySelectorAll('.weui-desktop-dialog__wrp')) {
                        if (wrp.offsetWidth === 0 && wrp.offsetHeight === 0) continue;
                        const title = wrp.querySelector('.weui-desktop-dialog__title');
                        if (!title || !title.textContent?.includes('原创权益')) continue;
                        const wrapper = wrp.querySelector('.ant-checkbox-wrapper, label.ant-checkbox-wrapper');
                        if (wrapper) { wrapper.click(); return { ok: true, method: 'ant-checkbox-wrapper' }; }
                        const cb = wrp.querySelector('input[type="checkbox"]');
                        if (cb) { cb.click(); return { ok: true, method: 'input' }; }
                        return { ok: false, error: '未找到勾选框' };
                    }
                    return { ok: false, error: '未找到原创权益弹窗' };
                `);

                if (checkResult.ok) {
                    console.log(`   ✅ 已勾选协议`);
                    await sleep(1000);

                    // 等待按钮可用 → 点击确认
                    for (let i = 0; i < 10; i++) {
                        await sleep(500);
                        const btnReady = await execInWujie(page, `
                            for (const wrp of doc.querySelectorAll('.weui-desktop-dialog__wrp')) {
                                if (wrp.offsetWidth === 0 && wrp.offsetHeight === 0) continue;
                                for (const b of wrp.querySelectorAll('button'))
                                    if (b.textContent?.trim() === '声明原创')
                                        return !b.disabled && !b.classList.contains('weui-desktop-btn_disabled');
                            }
                            return false;
                        `);
                        if (btnReady) {
                            await execInWujie(page, `
                                for (const wrp of doc.querySelectorAll('.weui-desktop-dialog__wrp')) {
                                    if (wrp.offsetWidth === 0 && wrp.offsetHeight === 0) continue;
                                    for (const b of wrp.querySelectorAll('button'))
                                        if (b.textContent?.trim() === '声明原创' && !b.disabled && !b.classList.contains('weui-desktop-btn_disabled'))
                                            { b.click(); return true; }
                                }
                                return false;
                            `);
                            console.log('   ✅ 已确认声明原创');
                            break;
                        }
                    }
                } else {
                    console.log(`   ⚠️ ${checkResult.error}`);
                }
            } catch (err) {
                console.log(`   ⚠️ ${err.message.substring(0, 80)}`);
            }

            // 6c: 处理可能的其他弹窗
            await sleep(3000);
            for (let extra = 0; extra < 3; extra++) {
                try {
                    const r = await execInWujie(page, `
                        for (const wrp of doc.querySelectorAll('.weui-desktop-dialog__wrp')) {
                            if (wrp.offsetWidth === 0 && wrp.offsetHeight === 0) continue;
                            for (const b of wrp.querySelectorAll('button')) {
                                const t = b.textContent?.trim();
                                if (['确认','确定','我知道了'].includes(t) && !b.disabled) { b.click(); return t; }
                            }
                        }
                        return null;
                    `);
                    if (r) { console.log(`   ✅ 已处理弹窗：「${r}」`); await sleep(2000); }
                    else break;
                } catch { break; }
            }

        } else {
            // ─── 直接发表流程 ───
            console.log('\n📌 Step 6：直接发表...');
            try {
                const r = await execInWujie(page, `
                    for (const wrp of doc.querySelectorAll('.weui-desktop-dialog__wrp')) {
                        if (wrp.offsetWidth === 0 && wrp.offsetHeight === 0) continue;
                        for (const b of wrp.querySelectorAll('button')) {
                            if (b.textContent?.trim() === '直接发表' && !b.disabled) { b.click(); return true; }
                        }
                    }
                    return false;
                `);
                console.log(r ? '   ✅ 已选择直接发表' : '   ⚠️ 未找到直接发表按钮');
            } catch (err) {
                console.log(`   ⚠️ ${err.message.substring(0, 80)}`);
            }
        }

        // ═══ Step 7：再次点击发表（声明原创后需要二次发表） ═══
        if (declareOriginal && page.url() === SPH_PUBLISH_URL) {
            console.log('\n📌 Step 7：提交发表...');
            await sleep(2000);

            try {
                await execInWujie(page, `
                    for (const b of doc.querySelectorAll('button'))
                        if (b.textContent?.trim() === '发表' && !b.disabled && !b.classList.contains('weui-desktop-btn_disabled'))
                            { b.click(); return true; }
                    return false;
                `);
                console.log('   ✅ 已提交');
            } catch (err) {
                console.log(`   ⚠️ ${err.message.substring(0, 80)}`);
            }

            // 等待页面跳转
            for (let i = 0; i < 15; i++) {
                await sleep(2000);
                if (page.url() !== SPH_PUBLISH_URL) {
                    console.log(`   ✅ 页面已跳转`);
                    break;
                }
                // 处理可能的弹窗
                try {
                    const r = await execInWujie(page, `
                        for (const wrp of doc.querySelectorAll('.weui-desktop-dialog__wrp')) {
                            if (wrp.offsetWidth === 0 && wrp.offsetHeight === 0) continue;
                            for (const b of wrp.querySelectorAll('button')) {
                                const t = b.textContent?.trim();
                                if (['确认','确定','我知道了','直接发表'].includes(t) && !b.disabled) { b.click(); return t; }
                            }
                        }
                        return null;
                    `);
                    if (r) console.log(`   ✅ 已处理弹窗：「${r}」`);
                } catch { }
            }
        }

        // 等待发布完成
        await sleep(5000);

        // ═══ 完成 ═══
        let afterUrl = page.url();
        if (afterUrl === SPH_PUBLISH_URL) {
            await page.goto('https://channels.weixin.qq.com/platform/post/list', { waitUntil: 'domcontentloaded' });
            await sleep(5000);
            afterUrl = page.url();
        }

        if (afterUrl.includes('/post/list')) {
            console.log('\n🎉 发布成功！');
        } else {
            console.log('\n⚠️ 请在视频号后台确认发布状态');
        }
        console.log('\n' + '═'.repeat(50));
        console.log('🎉 视频号发布流程完成！');
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
