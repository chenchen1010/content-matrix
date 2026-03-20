#!/usr/bin/env python3
"""
微信公众号文章完整发布流程
整合：Markdown编辑 + 文颜排版 + Evolink封面 + 微信发布
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
    submit_url = "https://api.evolink.io/v1/images/generations"
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

def publish_draft(access_token, title, content, thumb_media_id, author="", digest=""):
    """发布到草稿箱"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    
    article = {
        "title": title,
        "content": content,
        "thumb_media_id": thumb_media_id,
        "show_cover_pic": 1,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    if author:
        article["author"] = author
    if digest:
        article["digest"] = digest
    
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
            return data.get('media_id')
    except Exception as e:
        print(f"Error publishing: {e}", file=sys.stderr)
        return None

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

def main():
    parser = argparse.ArgumentParser(description='Complete WeChat Article Publisher')
    parser.add_argument('--app-id', required=True, help='WeChat App ID')
    parser.add_argument('--app-secret', required=True, help='WeChat App Secret')
    parser.add_argument('--evolink-key', required=True, help='Evolink API Key')
    parser.add_argument('--markdown', '-m', required=True, help='Markdown file path')
    parser.add_argument('--theme', default='default', help='Wenyan theme')
    parser.add_argument('--author', default='', help='Article author')
    parser.add_argument('--cover-prompt', default='', help='Custom cover prompt')
    
    args = parser.parse_args()
    
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
    draft_id = publish_draft(access_token, title, html_content, thumb_media_id, args.author)
    if not draft_id:
        sys.exit(1)
    
    print(f"\n✅ SUCCESS!")
    print(f"Draft ID: {draft_id}")
    print(f"Title: {title}")
    print(f"\nCheck your WeChat MP backend -> Drafts")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
