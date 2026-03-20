# RPA 输出指令规范

`extract_json_data` 解析 JSON 后，按以下格式输出变量，供 RPA 消费。

## 输出格式

每行一个变量：`变量名 % 值`

- 字符串：直接输出
- 列表：输出为 JSON 数组字符串，如 `["#上海家政", "#保洁推荐"]`
- 空值：输出空字符串

## 变量列表

| 变量名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `post_type` | str | 笔记类型 | `image_text` / `video` / `long_text` |
| `title` | str | 笔记标题 | `上海阿姨找对了，家里干净得像换了套房` |
| `content` | str | 正文内容 | `搬到上海三年...` |
| `tags` | list | 话题标签 | `["#上海家政", "#保洁推荐"]` |
| `files` | str | 文件路径，引号包裹、空格分隔 | `'/path/1.jpg' '/path/2.jpg'` |
| `cover_index` | int | 封面索引 | `0` |
| `location` | str | 地点 | `上海·浦东新区` |
| `mentions` | list | @用户 | `["@家政小王", "@上海生活指南"]` |
| `group_chat` | str | 群聊名称 | `家政交流群` |
| `schedule` | str | 定时发布时间 | `2026-03-20 09:00` |
| `product` | str | 关联商品 | `多功能清洁刷套装` |
| `file` | str | 笔记附件路径 | `'/path/attach.pdf'` |

## 输出示例

```
=== 小红书发布任务 - RPA 输出变量 ===
post_type % image_text
title % 上海阿姨找对了，家里干净得像换了套房
content % 搬到上海三年，换了5个保洁阿姨...
tags % ["#上海家政", "#保洁推荐", "#阿姨推荐", "#同城服务", "#家居清洁", "#生活小妙招", "#上海生活"]
files % '/Users/burning/Desktop/content/xhs/clean-home-01.jpg' '/Users/burning/Desktop/content/xhs/clean-home-02.jpg' '/Users/burning/Desktop/content/xhs/clean-home-03.jpg'
cover_index % 0
location % 上海·浦东新区
mentions % ["@家政小王", "@上海生活指南"]
group_chat % 家政交流群
schedule % 2026-03-20 09:00
product % 多功能清洁刷套装
file % /Users/burning/Desktop/content/xhs/cleaning-checklist.pdf
```

## RPA 消费方式

1. 调用 `extract_json_data(json_file_path)` 获取 dict
2. 或运行 `python extract_json_data.py <json_path>` 获取标准输出
3. 按变量名逐项填写小红书创作者页面
