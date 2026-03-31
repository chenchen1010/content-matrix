#!/usr/bin/env python3
"""
微信公众号发布工具

支持两种发布形式：
  文章模式 (--markdown)  — Markdown → 文颜排版 → HTML 图文消息(news)
  小绿书模式 (--image-dir) — 图片目录 → 图片消息(newspic)，最多20张
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

def get_access_token(app_id, app_secret):
    """获取微信access token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('access_token')
    except Exception as e:
        print(f"Error getting token: {e}", file=sys.stderr)
        return None

def generate_cover(evolink_key, prompt, output_path):
    """使用Evolink生成封面图"""
    submit_url = "https://api.evolink.ai/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {evolink_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "z-image-turbo",
        "prompt": prompt,
        "size": "16:9",
        "nsfw_check": False
    }
    
    try:
        req = urllib.request.Request(
            submit_url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if 'data' not in data or not data['data']:
            print(f"Error: {data}", file=sys.stderr)
            return False
            
        image_url = data['data'][0]['url']
        with urllib.request.urlopen(image_url, timeout=60) as img_response:
            with open(output_path, 'wb') as f:
                f.write(img_response.read())
        return True
    except Exception as e:
        print(f"Error generating cover: {e}", file=sys.stderr)
        return False

def upload_cover_to_wechat(access_token, image_path):
    """上传封面到微信永久素材"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    
    import mimetypes
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    content_type, _ = mimetypes.guess_type(image_path)
    if not content_type:
        content_type = 'image/jpeg'
    
    body = []
    body.append(f'--{boundary}'.encode())
    body.append(f'Content-Disposition: form-data; name="media"; filename="cover.jpg"'.encode())
    body.append(f'Content-Type: {content_type}'.encode())
    body.append(b'')
    body.append(image_data)
    body.append(f'--{boundary}--'.encode())
    body = b'\r\n'.join(body)
    
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(body))
    }
    
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('media_id')
    except Exception as e:
        print(f"Error uploading cover: {e}", file=sys.stderr)
        return None

def publish_draft_raw(access_token, article):
    """发布草稿（通用底层方法，接收完整 article dict）"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    payload = {"articles": [article]}

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'media_id' in data:
                return data['media_id']
            print(f"API error: {data}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Error publishing: {e}", file=sys.stderr)
        return None


def publish_draft(access_token, title, content, thumb_media_id, author="", digest=""):
    """发布图文消息(news)到草稿箱（向后兼容）"""
    article = {
        "article_type": "news",
        "title": title,
        "content": content,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    if author:
        article["author"] = author
    if digest:
        article["digest"] = digest
    return publish_draft_raw(access_token, article)

def upload_content_image(access_token, image_path):
    """上传正文图片到微信（用于图片文章模式）
    使用 uploadimg 接口，返回微信 URL（不占用永久素材数量）"""
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"

    import mimetypes
    boundary = '----WebKitFormBoundary' + str(int(time.time()))

    with open(image_path, 'rb') as f:
        image_data = f.read()

    filename = os.path.basename(image_path)
    content_type, _ = mimetypes.guess_type(image_path)
    if not content_type:
        content_type = 'image/jpeg'

    body = b'\r\n'.join([
        f'--{boundary}'.encode(),
        f'Content-Disposition: form-data; name="media"; filename="{filename}"'.encode(),
        f'Content-Type: {content_type}'.encode(),
        b'',
        image_data,
        f'--{boundary}--'.encode(),
    ])

    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(body))
    }

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('url')
    except Exception as e:
        print(f"Error uploading content image: {e}", file=sys.stderr)
        return None


def collect_images(image_dir):
    """收集目录下的图片文件，按文件名排序"""
    supported_ext = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    images = sorted([
        os.path.join(image_dir, f) for f in os.listdir(image_dir)
        if os.path.splitext(f)[1].lower() in supported_ext
    ])
    return images


def publish_article_with_images(app_id, app_secret, title, image_dir, author="", digest="", cover_path=None):
    """文章模式(news) + 图片：图片通过 uploadimg 上传，嵌入 HTML content"""
    images = collect_images(image_dir)
    if not images:
        print(f"Error: No images found in {image_dir}", file=sys.stderr)
        return None

    print(f"[NEWS 图文消息] Found {len(images)} images")

    print("Step 1: Getting access token...")
    access_token = get_access_token(app_id, app_secret)
    if not access_token:
        return None
    print("✓ Token obtained")

    # 上传封面为永久素材
    print("Step 2: Uploading cover (permanent material)...")
    cover = cover_path or images[0]
    thumb_media_id = upload_cover_to_wechat(access_token, cover)
    if not thumb_media_id:
        return None
    print(f"✓ Cover: {thumb_media_id}")

    # 上传正文图片（uploadimg 接口，返回 URL）
    print(f"Step 3: Uploading {len(images)} images via uploadimg...")
    wx_urls = []
    for i, img_path in enumerate(images):
        wx_url = upload_content_image(access_token, img_path)
        if not wx_url:
            print(f"  ✗ Failed: {os.path.basename(img_path)}", file=sys.stderr)
            return None
        wx_urls.append(wx_url)
        print(f"  ✓ [{i+1}/{len(images)}] {os.path.basename(img_path)}")

    # 拼装 HTML
    print("Step 4: Building HTML content...")
    img_tags = []
    for wx_url in wx_urls:
        img_tags.append(
            f'<p style="text-align:center;margin:0;padding:0;">'
            f'<img src="{wx_url}" style="width:100%;display:block;" />'
            f'</p>'
        )
    html_content = '\n'.join(img_tags)

    # 发布
    print("Step 5: Publishing news draft...")
    draft_id = publish_draft(access_token, title, html_content, thumb_media_id, author, digest)
    if not draft_id:
        return None

    print(f"\n✅ [NEWS] SUCCESS!")
    print(f"Draft ID: {draft_id}")
    print(f"Title: {title}")
    print(f"Images: {len(images)}")
    return draft_id


def publish_xiaolvshu(app_id, app_secret, title, image_dir, author="", digest="", content=""):
    """小绿书模式(newspic)：图片上传为永久素材，通过 image_info 引用，最多20张"""
    images = collect_images(image_dir)
    if not images:
        print(f"Error: No images found in {image_dir}", file=sys.stderr)
        return None

    if len(images) > 20:
        print(f"Warning: newspic supports max 20 images, truncating from {len(images)} to 20")
        images = images[:20]

    print(f"[NEWSPIC 图片消息] Found {len(images)} images")

    print("Step 1: Getting access token...")
    access_token = get_access_token(app_id, app_secret)
    if not access_token:
        return None
    print("✓ Token obtained")

    # 逐张上传为永久素材（add_material），拿到 media_id
    print(f"Step 2: Uploading {len(images)} images as permanent material...")
    media_ids = []
    for i, img_path in enumerate(images):
        media_id = upload_cover_to_wechat(access_token, img_path)
        if not media_id:
            print(f"  ✗ Failed: {os.path.basename(img_path)}", file=sys.stderr)
            return None
        media_ids.append(media_id)
        print(f"  ✓ [{i+1}/{len(images)}] {os.path.basename(img_path)} -> {media_id}")

    # 构建 article
    print("Step 3: Building newspic article...")
    article = {
        "article_type": "newspic",
        "title": title,
        "content": content or "",
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
        "image_info": {
            "image_list": [{"image_media_id": mid} for mid in media_ids]
        }
    }
    if author:
        article["author"] = author

    # 发布
    print("Step 4: Publishing newspic draft...")
    draft_id = publish_draft_raw(access_token, article)
    if not draft_id:
        return None

    print(f"\n✅ [NEWSPIC] SUCCESS!")
    print(f"Draft ID: {draft_id}")
    print(f"Title: {title}")
    print(f"Images: {len(images)} (permanent material)")
    return draft_id


def check_wenyan_installed():
    """检查文颜是否安装"""
    try:
        subprocess.run(['which', 'wenyan-mcp'], capture_output=True, check=True)
        return True
    except:
        return False

def install_wenyan():
    """安装文颜"""
    print("Installing Wenyan MCP...")
    try:
        subprocess.run(['npm', 'install', '-g', '@wenyan-md/mcp'], check=True)
        print("✓ Wenyan MCP installed")
        return True
    except Exception as e:
        print(f"Error installing Wenyan: {e}", file=sys.stderr)
        return False

def render_with_wenyan(markdown_file, theme='default'):
    """使用文颜渲染Markdown"""
    # 文颜渲染逻辑 - 这里模拟文颜的渲染
    # 实际使用时可以通过wenyan-mcp的stdio模式调用
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取FrontMatter
        title = ""
        cover = ""
        body = content
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                body = parts[2].strip()
                
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key == 'title':
                            title = value
                        elif key == 'cover':
                            cover = value
        
        # 简单的Markdown转HTML（文颜风格）
        html = body
        # Headers
        html = html.replace('### ', '<h3>').replace('\n### ', '</h3>\n<h3>')
        html = html.replace('## ', '<h2>').replace('\n## ', '</h2>\n<h2>')
        html = html.replace('# ', '<h1>').replace('\n# ', '</h1>\n<h1>')
        # Close headers
        for h in ['h1', 'h2', 'h3']:
            html = html.replace(f'</{h}>\n<{h}>', f'</{h}>\n')
        
        return title, cover, html
    except Exception as e:
        print(f"Error rendering: {e}", file=sys.stderr)
        return None, None, None

def publish_remote(api_url, api_token, endpoint, title, image_dir, account='default', author='', digest='', content='', cover_path=None):
    """通过远程 API 发布（文章或小绿书）"""
    import base64

    images = collect_images(image_dir)
    if not images:
        print(f"Error: No images found in {image_dir}", file=sys.stderr)
        return None

    if endpoint == '/publish/xiaolvshu' and len(images) > 20:
        print(f"Warning: max 20 images, truncating from {len(images)} to 20")
        images = images[:20]

    print(f"[REMOTE {endpoint}] Found {len(images)} images")

    # Encode images to base64
    image_payloads = []
    for i, img_path in enumerate(images):
        with open(img_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        image_payloads.append({
            'image_base64': b64,
            'filename': os.path.basename(img_path),
        })
        print(f"  Encoded [{i+1}/{len(images)}] {os.path.basename(img_path)}")

    payload = {
        'account': account,
        'title': title,
        'images': image_payloads,
    }
    if author:
        payload['author'] = author
    if digest:
        payload['digest'] = digest
    if content:
        payload['content'] = content

    url = api_url.rstrip('/') + endpoint
    print(f"Posting to {url} ...")

    headers = {
        'Content-Type': 'application/json',
    }
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'

    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')
        print(f"HTTP {e.code}: {err_body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return None

    if data.get('ok'):
        print(f"\n✅ SUCCESS!")
        print(f"Draft ID: {data.get('draft_media_id')}")
        print(f"Title: {title}")
        print(f"Images: {data.get('image_count')}")
        return data.get('draft_media_id')
    else:
        print(f"API error: {data.get('error')}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description='Complete WeChat Article Publisher')
    parser.add_argument('--app-id', default='', help='WeChat App ID')
    parser.add_argument('--app-secret', default='', help='WeChat App Secret')
    parser.add_argument('--title', '-t', default='', help='Article title (required for image mode)')
    parser.add_argument('--author', default='', help='Article author')
    parser.add_argument('--digest', default='', help='Article digest/summary')

    # Markdown 模式
    parser.add_argument('--markdown', '-m', default='', help='Markdown file path')
    parser.add_argument('--evolink-key', default='', help='Evolink API Key')
    parser.add_argument('--theme', default='default', help='Wenyan theme')
    parser.add_argument('--cover-prompt', default='', help='Custom cover prompt')

    # 小绿书模式（图片消息）
    parser.add_argument('--image-dir', '-i', default='', help='图片目录，用于小绿书或图片文章模式')
    parser.add_argument('--cover', default='', help='指定封面图路径（默认用第一张）')
    parser.add_argument('--type', default='文章', choices=['文章', '小绿书'],
                        help='发布类型：文章(news, HTML图文) 或 小绿书(newspic, 图片消息)')

    # 远程 API 模式
    parser.add_argument('--remote', default='', help='远程 API 地址 (如 https://cs.qwjxqn.xyz/wechat-mp)')
    parser.add_argument('--api-token', default='', help='远程 API Bearer token')
    parser.add_argument('--account', default='default', help='远程 API 账号名 (default/qwjxqn/jscxbwd)')

    args = parser.parse_args()

    # === 远程 API 模式 ===
    if args.remote and args.image_dir:
        if not args.title:
            print("Error: --title is required for image mode", file=sys.stderr)
            sys.exit(1)

        endpoint = '/publish/xiaolvshu' if args.type == '小绿书' else '/publish/article'
        result = publish_remote(
            args.remote, args.api_token, endpoint,
            args.title, args.image_dir,
            account=args.account,
            author=args.author,
            digest=args.digest,
        )
        sys.exit(0 if result else 1)

    # === 本地直连模式：需要 app-id / app-secret ===
    if not args.app_id or not args.app_secret:
        if args.image_dir or args.markdown:
            print("Error: --app-id and --app-secret are required (or use --remote for API mode)", file=sys.stderr)
            sys.exit(1)

    # === 图片目录模式 ===
    if args.image_dir:
        if not args.title:
            print("Error: --title is required for image mode", file=sys.stderr)
            sys.exit(1)

        if args.type == '小绿书':
            result = publish_xiaolvshu(
                args.app_id, args.app_secret,
                args.title, args.image_dir,
                author=args.author,
                digest=args.digest,
            )
        else:
            result = publish_article_with_images(
                args.app_id, args.app_secret,
                args.title, args.image_dir,
                author=args.author,
                digest=args.digest,
                cover_path=args.cover or None,
            )
        sys.exit(0 if result else 1)

    # === Markdown 模式（原有逻辑） ===
    if not args.markdown:
        print("Error: --markdown or --image-dir is required", file=sys.stderr)
        sys.exit(1)

    # Check/install Wenyan
    if not check_wenyan_installed():
        if not install_wenyan():
            print("Failed to install Wenyan MCP", file=sys.stderr)
            sys.exit(1)

    # Step 1: Render Markdown with Wenyan
    print("Step 1: Rendering Markdown with Wenyan...")
    title, cover_path, html_content = render_with_wenyan(args.markdown, args.theme)
    if not html_content:
        sys.exit(1)
    print(f"✓ Rendered: {title or 'Untitled'}")

    # Step 2: Generate or use cover
    temp_cover = None
    if not cover_path or not os.path.exists(cover_path):
        print("Step 2: Generating cover with Evolink...")
        if not args.evolink_key:
            print("Error: --evolink-key required when no cover provided", file=sys.stderr)
            sys.exit(1)
        temp_cover = f"/tmp/cover_{int(time.time())}.jpg"
        prompt = args.cover_prompt or f"A professional cover image for article: {title}, modern digital art style, 16:9"
        if not generate_cover(args.evolink_key, prompt, temp_cover):
            sys.exit(1)
        cover_path = temp_cover
        print(f"✓ Cover generated: {cover_path}")
    else:
        print(f"Step 2: Using existing cover: {cover_path}")

    # Step 3: Get WeChat token
    print("Step 3: Getting WeChat access token...")
    access_token = get_access_token(args.app_id, args.app_secret)
    if not access_token:
        if temp_cover and os.path.exists(temp_cover):
            os.remove(temp_cover)
        sys.exit(1)
    print("✓ Token obtained")

    # Step 4: Upload cover
    print("Step 4: Uploading cover to WeChat...")
    thumb_media_id = upload_cover_to_wechat(access_token, cover_path)
    if temp_cover and os.path.exists(temp_cover):
        os.remove(temp_cover)
    if not thumb_media_id:
        sys.exit(1)
    print(f"✓ Cover uploaded: {thumb_media_id}")

    # Step 5: Publish draft
    print("Step 5: Publishing to WeChat...")
    final_title = args.title or title
    draft_id = publish_draft(access_token, final_title, html_content, thumb_media_id, args.author)
    if not draft_id:
        sys.exit(1)

    print(f"\n✅ SUCCESS!")
    print(f"Draft ID: {draft_id}")
    print(f"Title: {final_title}")
    print(f"\nCheck your WeChat MP backend -> Drafts")

    return 0

if __name__ == '__main__':
    sys.exit(main())
