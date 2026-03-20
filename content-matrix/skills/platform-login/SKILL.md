# 平台登录引导

## 何时使用

当用户说「引导我登录」「帮我登录抖音 / 小红书」「开始登录」「不想复制终端命令」等，需要完成 **douyin_search** 或 **xiaohongshu-mcp** 的浏览器登录时。

## 助手必须遵守（重要）

1. **由助手代跑登录流程**：在终端中执行本 skill 下方「助手执行用命令」，**不要把整段 `cd ... && ./xxx.sh` 复制给用户去粘贴**。
2. **对用户的说明只写界面操作**：例如「正在启动登录助手 → 会弹出浏览器 → 请扫码/登录 → 成功后窗口会自动关闭」。必要时补充：终端里会打点或提示，**无需在终端输入内容**。
3. **可选提示（二选一即可）**：
   - Cursor / VS Code：**命令面板**（`Cmd+Shift+P` / `Ctrl+Shift+P`）→ **Tasks: Run Task** → 选 **「内容矩阵 · 抖音登录」** 或 **「内容矩阵 · 小红书登录」**（无需记路径）。
   - 或继续由助手直接执行下方命令。

## 工作区根目录判断

- 若当前工作区根目录是 **`content-matrix`**（能看到 `setup.sh`、`skills/`）：用 **A 组**路径。
- 若当前工作区根目录是 **`gstack`**（能看到 `content-matrix/` 子目录）：用 **B 组**路径。

## 助手执行用命令（勿整段发给用户）

### 抖音（douyin_search Cookie）

**A 组**（工作区 = content-matrix）：

```bash
cd "${WORKSPACE_ROOT}" && ./skills/tools/search/douyin/douyin-login.sh
```

**B 组**（工作区 = gstack）：

```bash
cd "${WORKSPACE_ROOT}/content-matrix" && ./skills/tools/search/douyin/douyin-login.sh
```

### 小红书（xiaohongshu-mcp 扫码）

**A 组**：

```bash
cd "${WORKSPACE_ROOT}" && ./skills/tools/search/xiaohongshu/bin/xiaohongshu-login
```

**B 组**：

```bash
cd "${WORKSPACE_ROOT}/content-matrix" && ./skills/tools/search/xiaohongshu/bin/xiaohongshu-login
```

> 执行前将 `${WORKSPACE_ROOT}` 换为实际工作区根路径；助手应自行解析，勿要求用户替换变量。

## 登录成功后

- 抖音：可执行 `mcporter call 'douyin_search.check_login_status()'` 代用户确认。
- 小红书：提醒用户再启动 MCP（仍可由助手执行 `xiaohongshu-mcp` 或指导使用任务 **「启动小红书 MCP」**）。

## 对用户示例话术

```
正在帮你启动抖音登录助手，稍后会自动打开浏览器。
请在窗口里完成登录（扫码或账号密码）；检测到登录成功后，脚本会自动保存 Cookie 并关闭浏览器，
你不需要在终端里输入任何东西。

若你更习惯自己点菜单：Cmd+Shift+P → 「运行任务」→ 选「内容矩阵 · 抖音登录」也可以。
```
