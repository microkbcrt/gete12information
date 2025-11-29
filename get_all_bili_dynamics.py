# get_all_bili_dynamics.py
import requests
import json
from datetime import datetime
import os
import time
import random

# --- 【统一配置区】 ---
TARGET_USERS = [
    {"name": "F1", "mid": "65125803"},
    {"name": "genshin", "mid": "401742377"},
    {"name": "honkai", "mid": "1340190821"},
    {"name": "phigros", "mid": "414149787"},
    {"name": "ruixue", "mid": "258614728"},
    {"name": "tastecar", "mid": "386205726"},
    {"name": "zzz", "mid": "1636034895"},
]
OUTPUT_FILENAME = 'dynamics.json'
SESSDATA = os.environ.get('BILI_SESSDATA')

def parse_dynamic_item(item):
    """
    专门解析 Desktop API 返回的 items 结构 (modules 是个 list)
    """
    try:
        id_str = item.get('id_str')
        modules = item.get('modules', [])
        
        # 1. 提取发布时间 (从 module_author)
        pub_ts = 0
        for mod in modules:
            if 'module_author' in mod:
                pub_ts = mod['module_author'].get('pub_ts', 0)
                break
        
        # 2. 提取文本内容 (从 module_desc)
        text_content = ""
        for mod in modules:
            if 'module_desc' in mod:
                text_content = mod['module_desc'].get('text', "")
                break
        
        # 3. 提取视频/富媒体信息 (从 module_dynamic)
        # 你的JSON显示有 dyn_archive (视频), dyn_draw (图文), dyn_forward (转发)
        video_info = ""
        for mod in modules:
            if 'module_dynamic' in mod:
                dynamic_data = mod['module_dynamic']
                
                # 情况A: 这是一个视频 (dyn_archive)
                if 'dyn_archive' in dynamic_data:
                    archive = dynamic_data['dyn_archive']
                    title = archive.get('title', '')
                    desc = archive.get('desc', '')
                    video_info = f"\n【视频标题】: {title}\n【视频简介】: {desc}"
                
                # 情况B: 这是一个转发 (dyn_forward)
                elif 'dyn_forward' in dynamic_data:
                    # 转发的内容通常在 module_desc 里已经有了，这里可以标记一下
                    video_info = "\n[这是一条转发动态]"
        
        # 组合最终内容
        final_content = text_content + video_info
        
        return {
            "id": id_str,
            "pub_ts": pub_ts,
            "content": final_content.strip()
        }
        
    except Exception as e:
        print(f"  解析单条动态时出错: {e}")
        return None

def fetch_latest_dynamic_for_user(host_mid, base_headers):
    """
    使用 Desktop API 获取，并适配 List 结构的 modules
    """
    list_api_url = "https://api.bilibili.com/x/polymer/web-dynamic/desktop/v1/feed/space"
    
    params = {
        "host_mid": host_mid,
        "offset": "", 
        "timezone_offset": "-480",
        "features": "itemOpusStyle"
    }

    current_headers = base_headers.copy()
    current_headers['Referer'] = f'https://space.bilibili.com/{host_mid}/dynamic'

    try:
        response = requests.get(list_api_url, headers=current_headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            print(f"  API报错: {data.get('message')}")
            return None

        items_list = data.get('data', {}).get('items')
        if not items_list:
            print(f"  用户(UID: {host_mid}) 暂无动态。")
            return None

        # --- 【修复核心】 ---
        # 你的报错是因为代码试图用 .get() 去操作 list
        # 现在我们先解析所有动态，再按时间排序
        parsed_items = []
        for item in items_list:
            parsed = parse_dynamic_item(item)
            if parsed:
                parsed_items.append(parsed)
        
        if not parsed_items:
            print("  未能解析出任何有效动态。")
            return None

        # 找到最新的
        latest_post = max(parsed_items, key=lambda x: x['pub_ts'])
        
        publish_time_str = datetime.fromtimestamp(latest_post['pub_ts']).strftime('%Y-%m-%d %H:%M:%S')
        dynamic_url = f"https://www.bilibili.com/opus/{latest_post['id']}"

        return {
            "publish_time": publish_time_str,
            "dynamic_url": dynamic_url,
            "content": latest_post['content']
        }

    except Exception as e:
        print(f"  请求异常 (UID: {host_mid}): {e}")
        return None

def main():
    if not SESSDATA:
        print("错误：环境变量 BILI_SESSDATA 未设置！")
        exit(1)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Cookie': f'SESSDATA={SESSDATA}',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://space.bilibili.com',
        'Connection': 'keep-alive'
    }

    all_dynamics_data = {}
    print("🚀 开始获取所有目标用户的最新B站动态 (Desktop List 模式)...")

    for user in TARGET_USERS:
        user_name = user['name']
        user_mid = user['mid']
        print(f"\n--- 正在处理用户: {user_name} (UID: {user_mid}) ---")
        
        dynamic_data = fetch_latest_dynamic_for_user(user_mid, headers)
        
        if dynamic_data:
            all_dynamics_data[user_name] = dynamic_data
            print(f"✅ 成功: {user_name} | 时间: {dynamic_data['publish_time']}")
        else:
            print(f"❌ 失败: {user_name}")
        
        time.sleep(random.uniform(2, 4))

    if not all_dynamics_data:
        print("\n⚠️ 未获取到数据。")
        return

    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(all_dynamics_data, f, ensure_ascii=False, indent=4)
        print(f"\n🎉 完成！已保存至 {OUTPUT_FILENAME}")
    except Exception as e:
        print(f"文件写入错误: {e}")

if __name__ == "__main__":
    main()
