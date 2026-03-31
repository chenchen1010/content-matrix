---
name: framework-sync
description: 检查主框架更新并一键同步到本地，非技术用户无需了解 git 操作
---

# 框架同步（Framework Sync）

## 触发时机

### 自动触发：每次会话开始时
在用户开始使用任何 content-matrix 功能前，先运行更新检查：

```bash
_UPD=$(bash content-matrix/scripts/check-update.sh 2>/dev/null || true)
```

根据输出决定下一步：

- **输出 `UP_TO_DATE`** → 不做任何提示，直接进入用户的工作
- **输出 `UPGRADE_AVAILABLE <本地版本> <远程版本>`** → 执行下方「更新提醒流程」

### 手动触发：用户说"同步"、"更新"、"检查更新"

## 更新提醒流程

当检测到新版本时，用中文向用户展示：

```
📦 内容矩阵框架有新版本！

当前版本：{本地版本}
最新版本：{远程版本}

更新内容：
{CHANGELOG 中的最新变更摘要}
```

然后用 AskUserQuestion 询问用户，提供以下选项：
1. **"好的，帮我更新"** → 执行同步
2. **"先不更新，继续工作"** → 跳过，继续用户原本的任务
3. **"以后都自动更新"** → 记住偏好后执行同步

## 同步执行步骤

### 步骤 1：检测安装类型

```bash
cd {项目根目录}
git remote -v
```

判断当前仓库的 upstream 情况：

- **有 upstream remote** → 这是一个 fork，从 upstream 拉取
- **只有 origin** → 需要先添加 upstream

### 步骤 2：确保 upstream 指向主仓库

```bash
# 检查是否已有 upstream
git remote get-url upstream 2>/dev/null
```

如果没有 upstream，添加：
```bash
git remote add upstream https://github.com/chenchen1010/content-matrix.git
```

### 步骤 3：拉取并合并

```bash
# 获取主仓库最新代码
git fetch upstream main

# 先提交用户本地的未保存修改（如有）
git add -A && git commit -m "保存本地修改" 2>/dev/null || true

# 合并主仓库更新
git merge upstream/main --no-edit
```

### 步骤 4：处理冲突

如果合并产生冲突：

1. **不要慌张，不要让用户处理**
2. 读取冲突文件，理解双方改动的意图
3. 智能合并：保留用户的业务定制 + 融入主框架的新功能
4. 完成后提交：
```bash
git add -A && git commit -m "合并主框架更新，保留本地定制"
```

### 步骤 5：更新本地 VERSION

确认 VERSION 文件已更新为最新版本。

### 步骤 6：向用户报告

用中文简洁说明：
- 更新了什么（从 CHANGELOG 提取要点）
- 用户的本地定制是否保留完好
- 如有冲突，说明如何解决的

## 用户偏好存储

如果用户选择了"以后都自动更新"，在项目根目录 `.gstack/config.yaml` 中记录：

```yaml
auto_sync: true
```

下次会话检测到更新时，跳过询问，直接执行同步。

## 注意事项

- **绝不删除用户的本地文件或修改**
- 冲突时优先保留用户的业务内容，再叠加框架新功能
- 如果网络不通，静默跳过，不要报错打断用户
- output/ 目录下的内容永远不参与同步（已在 .gitignore 中排除）
