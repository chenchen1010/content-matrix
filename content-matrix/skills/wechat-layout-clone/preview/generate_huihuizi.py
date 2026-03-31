#!/usr/bin/env python3
"""
生成「惠惠子」风格公众号样式预览。

风格来源：《病，是主体性的一部分｜心理咨询师手记02》— 惠惠子心理 (彭惠琳)
风格特征：紧凑、两端对齐、13px 小字、粉色章节号、灰色正文、每句一段

- 正文用 **双星号** 标记需加粗的重点。
- 章节用 ## 标记（如 ##01），会渲染为粉色居中编号。
- 空行用 --- 标记，会生成空 <p> 分隔。
"""
from __future__ import annotations

import re
from html import escape
from pathlib import Path

# ── 惠惠子风格 CSS 参数 ──────────────────────────────────────
# 外层 <p> / <span> 的基础样式
P_STYLE = (
    "margin: 0px 8px 24px; padding: 0px; clear: both; min-height: 1em; "
    "color: rgba(0, 0, 0, 0.9); "
    'font-family: "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, '
    '"Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", '
    "Arial, sans-serif; font-size: 17px; letter-spacing: 0.544px; "
    "text-align: justify; line-height: 1.5em"
)

P_CENTER = (
    "margin: 0px 8px 24px; padding: 0px; clear: both; min-height: 1em; "
    "color: rgba(0, 0, 0, 0.9); "
    'font-family: "PingFang SC", system-ui, -apple-system, BlinkMacSystemFont, '
    '"Helvetica Neue", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", '
    "Arial, sans-serif; font-size: 17px; letter-spacing: 0.544px; "
    "text-align: center; line-height: 1.5em"
)

# 正文内层 span
INNER = "font-size: 13px; color: rgb(76, 75, 75)"
BOLD = "font-size: 13px; color: rgb(76, 75, 75); font-weight: bold"

# 章节编号（黑底粉字居中）
SECTION_NUM = "font-size: 13px; background-color: rgb(0, 0, 0); color: rgb(255, 172, 213); font-weight: bold"


def fmt_inline_bold(s: str) -> str:
    """将 **重点** 转为带内联样式的 span，其余 HTML 转义。"""
    parts = re.split(r"(\*\*.+?\*\*)", s)
    chunks: list[str] = []
    for p in parts:
        if len(p) >= 4 and p.startswith("**") and p.endswith("**"):
            inner = p[2:-2]
            chunks.append(f'<span style="{BOLD}">{escape(inner)}</span>')
        else:
            chunks.append(escape(p))
    return "".join(chunks)


def block_body(text: str) -> str:
    """普通正文段落：两端对齐 + 灰色 13px。"""
    inner = fmt_inline_bold(text)
    return (
        f'<p style="{P_STYLE}">'
        f'<span style="{INNER}">{inner}</span>'
        f"</p>"
    )


def block_section_num(num: str) -> str:
    """章节编号：居中粉色。"""
    return (
        f'<p style="{P_CENTER}">'
        f'<span style="{SECTION_NUM}">{escape(num)}</span>'
        f"</p>"
    )


def block_empty() -> str:
    """空行分隔。"""
    return f'<p style="{P_STYLE}"><br/></p>'


def block_img(src: str, alt: str = "") -> str:
    """插入配图。"""
    return (
        f'<div style="margin: 0 8px 24px; padding: 0">'
        f'<img style="display: block; width: 100%; border-radius: 4px" src="{escape(src)}" alt="{escape(alt)}"/>'
        f"</div>"
    )


# ── 文章内容 ──────────────────────────────────────────────
# 特殊标记：
#   ##XX       → 章节编号（黑底粉字居中）
#   ---        → 空行分隔
#   ![alt](src) → 配图
#   其余       → 正文段落
PARAS = [
    "##01",
    "![封面图：影子里开出花朵](images-huihuizi/cover.png)",
    "在笛卡尔的二元视角里，身体常常被看作是一架机器，**病是机器的故障**。",
    "医生的任务，就是修理这台机器——切除病灶、杀死细菌病毒、置换坏掉的零件。",
    "于是，病被简化为**「异常的指标」**，是完全**「异己的存在」**。",
    "这套逻辑也被沿用到心理疾病/心理症状的领域。",
    "有的人来做心理咨询，主诉就是「请帮我去除XXX的症状」「我不想再有XXX的感受了」。",
    "但是做咨询了这么久，我越来越萌生出一些不一样的看法。",
    "---",
    "**病有时是尝试自愈的药。**",
    "比如强迫行为看似荒谬，却为混乱的内心建立了秩序；抑郁让人停滞，却阻止了更多能量的消耗；多疑虽然偏执，但是却曾经在许多次危机中保护过自身。",
    "病本是药，过量则成了毒。",
    "![配图：金缮碗，裂缝中长出新芽](images-huihuizi/illustration-1-medicine.png)",
    "**病有时是一种发声。**",
    "为那些不曾言说，不曾被正视，不曾被好好对待的感受，发出无法被忽视的声音。不仅仅是为了自身听到，更是为了个体所处的环境能听到。",
    "只有被听到，沉冤的才能被昭雪，蒙尘的才能重见天日。",
    "**病有时是配平的砝码。**",
    "如果个体所处的环境，在某种微妙的失衡状态里，那么系统会选中其中某位成员，担当病的承载者。",
    "比如一个家庭，父母长辈都是很情绪隔离，表演乐观积极，幸福快乐，那么孩子很有可能就走向天平的另一端，变得敏感脆弱，消极悲观。",
    "**病有时亦是盛大的追悼和铭记。**",
    "个体的创伤，民族的集体创伤，那些无法被释怀的苦难记忆，也会以病的形式显现。",
    "症状就成了一种隐秘的历史书写方式，一种不需要语言的记忆传承，提醒着我们勿忘来时路，来时路是塑造今时我的一部分。",
    "**病有时还会变成反抗的旗帜。**",
    "福柯曾说，疯癫是被社会定义出来的。当某种状态被定义为病时，这背后往往隐藏着权力的运作。那些对权威、系统构成威胁的，就被病理化、边缘化。",
    "而病就成了自我存在的一种确认方式，「我怎么活是我的事情」，「我病故我在」。",
    "---",
    "我还很喜欢佛门对于病的理解。",
    "**维摩诘示疾，「从痴有爱，则我病生」。**",
    "——病因无明而起，因执着而在，是无尽因缘和合的产物。",
    "其中千丝万缕，都是与「我」相关。「无我」，则病亦失去了挂碍。",
    "但毕竟不是所有人都要成佛成圣，普通人的人生，不就是借助「痴」与「爱」的苦，去体验那个自我的存在吗。",
    "---",
    "庄子里有个故事，云：",
    "人有畏影恶迹而去之走者，举足愈数而迹愈多，走愈疾而影不离身。自以为尚迟，疾走不休，绝力而死。不知处阴以休影，处静以息迹，愚亦甚矣！",
    "大概意思是，有人害怕并且厌恶自己的影子和脚印，想要摆脱它们，就快不跑起来，可是无论跑多快都甩不掉，最后力竭而死。",
    "**病其实也是那个影子。**",
    "**如果我们不跑，我们回头看，就可以看见它是我们自身投下的阴影，也没有那么可怕嘛。**",
    "![配图：庄子寓言，树下与影子和解](images-huihuizi/illustration-2-shadow.png)",
    "---",
    "##02",
    "最近在看有关量子物理的科普，里面提到，在量子世界里，一个粒子未被观测时的状态，包含了它所有可能性的信息，是一种模糊的、弥散的、概率性的存在，是所有这些可能性的叠加。",
    "而一旦进行了观测，所有的可能性就会瞬间坍缩到一个确定的点上。",
    '那如果把个体的整个心灵世界想象成一个\u201c量子场\u201d，潜意识会不会就像是量子的\u201c状态云\u201d。',
    '潜意识是心理活动的基础，储存了记忆，欲望、创伤，本能冲动、未分化的情感和想法等等，它的内容是模糊的、象征性的、非逻辑的，无法直接、清晰的感知，也无法言说。',
    '当我们在发呆、冥思、做梦的时候，把\u201c我\u201d给放空了，那就进入到这个广阔无垠的领域。它无边无界，包含了所有可能性的版本，就像是多重自我的叠加态，无所不有，应有尽有。',
    '它不住于某一个相。它是无相，也是万相。',
    "![配图：量子叠加态的多重自我](images-huihuizi/illustration-3-quantum.png)",
    '当你把意识的探照灯（测量）打向潜意识某个特定区域之后，这种状态才会\u201c坍缩\u201d，成为你实际体验到的一个具体念头或情绪。这些东西才有了命名，有了意义，有了秩序。',
    '同时，当一个人独处的时候，他的自我可能是流动的、复杂的、充满内在矛盾和潜能的，没有单一的定义。',
    '当个体与他者进入一段关系时，关系的互动（他人的目光、言语、期待或行为）就像一次测量，迫使流动的自我必须呈现出某个特定的面貌、角色或特质。',
    '于是，一个具体的自我，在关系中被共同构建出来。',
    '同一个人，在不同的关系中，会展现出截然不同的自我。',
    '这就完美的解释了，为什么我们在不同的人面前感觉变了一个人似的。',
    "**因为我们本来就是一个充满可能性的状态云，是关系的情景，决定了哪一个可能性成为了暂时的现实。**",
]


IMG_RE = re.compile(r"^!\[(.*)]\((.+)\)$")


def main() -> None:
    parts: list[str] = []
    for p in PARAS:
        if p.startswith("##"):
            parts.append(block_section_num(p[2:]))
        elif p == "---":
            parts.append(block_empty())
        elif (m := IMG_RE.match(p)):
            parts.append(block_img(m.group(2), m.group(1)))
        else:
            parts.append(block_body(p))
    body = "\n".join(parts)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0,viewport-fit=cover"/>
<title>排版预览 · 惠惠子风格</title>
<style>
  html {{ -webkit-text-size-adjust: 100%; }}
  body {{
    margin: 0;
    background: #ededed;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    padding: 12px 0 32px;
  }}
  .phone {{
    max-width: 677px;
    margin: 0 auto;
    background: #fff;
    min-height: 100vh;
    box-shadow: 0 0 12px rgba(0,0,0,.06);
  }}
  .meta {{
    padding: 20px 16px 8px;
    border-bottom: 1px solid #e7e7e7;
  }}
  .meta h1 {{
    font-size: 22px;
    font-weight: 700;
    line-height: 1.4;
    margin: 0 0 8px;
    color: #111;
  }}
  .meta .sub {{ font-size: 14px; color: #888; margin: 0; line-height: 1.5; }}
  #js_content {{
    padding: 16px 0 40px;
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }}
  #js_content p {{
    margin: 0;
    padding: 0;
  }}
</style>
</head>
<body>
<div class="phone">
  <div class="meta">
    <h1>病，是主体性的一部分｜心理咨询师手记02</h1>
    <p class="sub">风格来源：<strong>惠惠子心理</strong>（彭惠琳）。用 <code>**…**</code> 加粗，<code>##01</code> 粉色章节号，<code>---</code> 空行分隔。改完运行 <code>python3 generate_huihuizi.py</code>。</p>
  </div>
  <div id="js_content" class="rich_media_content js_underline_content autoTypeSetting24psection">
{body}
  </div>
</div>
</body>
</html>
"""

    out = Path(__file__).with_name("huihuizi-wechat-layout.html")
    out.write_text(html, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
