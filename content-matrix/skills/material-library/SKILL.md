# 素材库路由

素材管理的入口层，根据用户配置自动选择素材存储方案。

## 路由逻辑

```
检查 obsidian-cli 是否可用：
  obsidian-cli print-default --path-only 2>/dev/null

├─ 可用 → 使用 obsidian-kb skill（Obsidian 知识库）
└─ 不可用 → 检查飞书配置
    ├─ ~/.content-organizer/config.json 存在 → 使用飞书多维表格
    └─ 都没有 → 提示用户选择并配置
```

## 何时使用

当用户说"帮我管理素材"、"录入素材"、"找素材"时，先运行路由逻辑判断使用哪个后端。

## Obsidian 路径（推荐）

检测到 obsidian-cli 可用时，转交 `obsidian-kb` skill 处理。

详见 `obsidian-kb/SKILL.md`。

## 飞书路径

检测到飞书配置时，通过飞书 API 读写素材。

### 读取飞书素材
```bash
CONFIG_FILE=~/.content-organizer/config.json

APP_ID=$(jq -r '.app_id' "$CONFIG_FILE")
APP_SECRET=$(jq -r '.app_secret' "$CONFIG_FILE")
TOKEN_RESP=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"$APP_ID\",\"app_secret\":\"$APP_SECRET\"}")
TOKEN=$(echo "$TOKEN_RESP" | jq -r '.tenant_access_token')

APP_TOKEN=$(jq -r '.app_token' "$CONFIG_FILE")
TABLE_ID=$(jq -r '.table_id' "$CONFIG_FILE")
curl -s "https://open.feishu.cn/open-apis/bitable/v1/apps/$APP_TOKEN/tables/$TABLE_ID/records?page_size=20" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.items'
```

### 写入飞书素材
使用 `content-organizer` skill 的能力写入飞书多维表格。

## 快捷用法

- "录入一个客户案例" → 路由判断后执行对应 skill
- "从飞书拉素材" → 直接走飞书路径
- "从知识库找素材" → 直接走 Obsidian 路径
