# RPA 兼容性说明

本文档记录 `extract_json_data.py` 在 RPA 环境中调试的经验，供后续维护参考。

## 1. RPA 与标准 Python 的差异

| 项目 | 标准 Python | RPA 环境 |
|------|-------------|----------|
| `except` 写法 | `except Exception:` | `except:`（裸 except） |
| 类型注解 | 推荐使用 `def f(x: str) -> dict` | 建议去掉，避免解析错误 |
| `typing` 模块 | 可用 `from typing import *` | 建议移除，减少依赖 |
| 空 `except` 块 | 需 `pass` 或具体处理 | 可能触发「expected an indented block」 |

## 2. 常见错误与修复

### 2.1 输出变量名而非实际值

**现象**：RPA 调试变量中，`笔记标题` 显示为 `'title'` 而不是 `"上海阿姨找对了..."`。

**原因**：RPA 按「变量名 % 值」解析输出时，若格式或变量名不匹配，会拿到 key 名而不是 value。

**处理**：确保 docstring 中的 `% 变量名 %` 与 RPA 期望的中文变量名一致，且函数返回的是实际值（如 `json_data.get("title")`），而不是字符串 `"title"`。

### 2.2 第 16 行缩进错误

**现象**：`源代码第【16】行出错：^, expected an indented block`。

**可能原因**：
- `try/except` 中 `except` 后缺少可执行语句
- 多层 `try/except` 嵌套导致 RPA 解析异常
- 类型注解或复杂语法触发 RPA 解析问题

**处理**：
- 使用 `except:` 而不是 `except Exception:`
- 简化 `try/except` 结构，只保留一层
- 去掉类型注解和 `typing` 导入

## 3. RPA 兼容写法建议

1. **导入**：仅保留 `import json`，去掉 `from typing import *`。
2. **异常**：`except` 块内至少有一行有效代码（如 `from xbot import print`），避免「expected an indented block」。
3. **函数签名**：`def extract_json_data(json_file_path):`，不加类型注解。
4. **辅助函数**：为 `_to_str`、`_to_int` 等加简短 docstring，便于 RPA 理解。
5. **调试输出**：对关键字段（如 `location`）增加 `print`，便于在 RPA 中排查问题。
6. **返回格式**：保持 13 个元素的元组返回，顺序与 docstring 中 outputs 一致。

## 4. 复制到 RPA 前的检查清单

- [ ] 已移除 `typing` 相关导入和类型注解
- [ ] `except` 使用裸 `except:` 且块内非空
- [ ] docstring 中 outputs 与 RPA 变量名一一对应
- [ ] 本地运行 `python extract_json_data.py <json_path>` 无报错
- [ ] 返回元组顺序与 RPA 解包顺序一致

## 5. 调试输出说明

当前脚本会输出：

- `当前输入：{json_file_path}`
- `笔记标题是 {title}`
- `地点原始值: {location_raw}`
- `地点最终值: {location}`
- `JSON文件中包含的字段: [...]`

发布环境可酌情删除或注释这些 `print`，以降低日志噪音。
