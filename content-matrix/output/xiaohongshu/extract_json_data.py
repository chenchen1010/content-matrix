"""
小红书发布任务 JSON 解析器（RPA 兼容版）

从 JSON 文件中提取笔记信息，输出供 RPA 填写的变量。
与 post-schema.json 字段一一对应。

RPA 兼容性说明见同目录 RPA_兼容性说明.md
"""

import json

try:
    from xbot.app.logging import trace as print
except Exception:
    try:
        from xbot import print
    except Exception:
        print = __import__("builtins").print  # 非 RPA 环境回退


def extract_json_data(json_file_path):
    """
    title: 提取JSON文件中的笔记信息
    description: 从JSON文件中提取笔记标题 % title %、正文内容 % content %、话题标签 % tags %、文件地址 % files %、群聊 % group_chat %、关联地址 % related_url %、定时发布时间 % scheduled_time %、关联商品 % related_products %、笔记类型 % post_type %、封面索引 % cover_index %、地点 % location %、@用户列表 % mentions %、笔记附件 % file % 等一级字段信息，分别作为独立变量输出。
    inputs:
        - json_file_path (file): JSON数据文件路径，eg: "data.json"
    outputs:
        - title (str): 笔记标题，eg: "我的旅行日记"
        - content (str): 正文内容，eg: "今天去了美丽的海边..."
        - tags (list): 话题标签列表，eg: ["#旅行", "#海边", "#美食"]
        - files (str): 文件地址文本格式，eg: "'/path/to/image1.jpg' '/path/to/image2.jpg'"
        - group_chat (str): 群聊信息，eg: "旅行分享群"
        - related_url (str): 关联地址，eg: ""
        - scheduled_time (str): 定时发布时间，eg: "2026-03-20 09:00"
        - related_products (str): 关联商品，eg: "旅行背包"
        - post_type (str): 笔记类型，eg: "image_text"
        - cover_index (int): 封面索引，eg: 0
        - location (str): 地点，eg: "上海·浦东新区"
        - mentions (list): @用户列表，eg: ["@家政小王"]
        - file (str): 笔记附件路径，eg: "/path/attach.pdf"
    """
    if not json_file_path:
        raise ValueError("JSON文件路径不能为空")

    def _read_json_file(file_path):
        """读取JSON文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"找不到文件: {file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"文件格式错误，无法解析JSON: {file_path}")

    def _format_files_list(files_data):
        """将文件地址列表转换为文本格式：每个路径用引号包裹，空格分隔"""
        if not files_data:
            return ""
        if isinstance(files_data, list):
            return " ".join(f"'{str(p).strip()}'" for p in files_data if p)
        if isinstance(files_data, str):
            paths = [p.strip().strip("'\"") for p in files_data.split() if p.strip()]
            return " ".join(f"'{p}'" for p in paths)
        return f"'{files_data}'"

    def _to_str(val, default=""):
        """将值转换为字符串"""
        if val is None:
            return default
        return str(val).strip() if val else default

    def _to_int(val, default=0):
        """将值转换为整数"""
        if val is None:
            return default
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    # 读取JSON文件
    json_data = _read_json_file(json_file_path)

    # 打印当前输入文件路径
    print(f"当前输入：{json_file_path}")

    # 提取笔记标题
    title = _to_str(json_data.get("title"))
    print(f"笔记标题是 {title}")

    # 提取正文内容
    content = _to_str(json_data.get("content"))

    # 提取话题标签（转换为list，每项含#）
    tags_data = json_data.get("tags", [])
    tags = tags_data if isinstance(tags_data, list) else ([tags_data] if tags_data else [])

    # 提取文件地址并转换为文本格式
    files_data = json_data.get("files", [])
    files = _format_files_list(files_data)

    # 提取群聊信息
    group_chat = _to_str(json_data.get("group_chat"))

    # 提取关联地址（预留，当前schema无此字段）
    related_url = _to_str(json_data.get("related_url"))

    # 提取定时发布时间（兼容schedule/scheduled_time）
    scheduled_time = _to_str(json_data.get("schedule") or json_data.get("scheduled_time"))

    # 提取关联商品（兼容product/related_products）
    related_products = _to_str(json_data.get("product") or json_data.get("related_products"))

    # 提取笔记类型
    post_type = _to_str(json_data.get("post_type"), "image_text")

    # 提取封面索引
    cover_index = _to_int(json_data.get("cover_index"), 0)

    # 提取地点
    location_raw = json_data.get("location")
    print(f"地点原始值: {location_raw}")
    location = _to_str(location_raw)
    print(f"地点最终值: {location}")

    # 提取@用户列表（list，每项含@）
    mentions_raw = json_data.get("mentions", [])
    mentions = mentions_raw if isinstance(mentions_raw, list) else ([mentions_raw] if mentions_raw else [])

    # 提取笔记附件
    file = _to_str(json_data.get("file"))

    # 打印JSON文件中的所有键，帮助调试
    print(f"JSON文件中包含的字段: {list(json_data.keys())}")

    return (
        title,
        content,
        tags,
        files,
        group_chat,
        related_url,
        scheduled_time,
        related_products,
        post_type,
        cover_index,
        location,
        mentions,
        file,
    )
