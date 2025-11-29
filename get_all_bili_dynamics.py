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

def get_content_from_detail_api(dynamic_id, headers):
    """
    获取动态详情。
    """
    detail_api_url = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail"
    params = {"dynamic_id": dynamic_id}
    
    try:
        # 详情页 API 通常不需要特别复杂的参数，但为了稳妥，带上基础 headers
        response = requests.get(detail_api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') == 0 and data.get('data', {}).get('card'):
            card_str = data['data']['card'].get('card')
            card_data = json.loads(card_str)
            
            # 1. 图文
            description = card_data.get('item', {}).get('description')
            if description:
                return description.strip()
            
            # 2. 纯文本
            content = card_data.get('item', {}).get('content')
            if content:
                return content.strip()
            
            # 3. 视频
            title = card_data.get('title')
            video_desc = card_data.get('desc')
            dynamic_text = card_data.get('dynamic', '')
            if title and video_desc is not None:
                final_text = f"投稿了视频：【{title}】\n\n{dynamic_text}\n\n视频简介：\n{video_desc}"
                return final_text.strip()

            if dynamic_text:
                 return dynamic_text.strip()
            
            return None
        else:
            return None
            
    except Exception as e:
        print(f"  [详情API异常] {e}")
        return None

def fetch_latest_dynamic_for_user(host_mid, base_headers):
    """
    使用最新的 Desktop API 获取用户动态
    """
    # --- 【修改点 1】 使用 Desktop 版本的 API ---
    list_api_url = "https://api.bilibili.com/x/polymer/web-dynamic/desktop/v1/feed/space"

    # --- 【修改点 2】 补全关键参数 ---
    # 根据你提供的文档，timezone_offset 是必须的，模拟东八区(-480分钟)
    # features 用于指定返回格式，网页端常带这个
    params = {
        "host_mid": host_mid,
        "offset": "", 
        "timezone_offset": "-480",
        "features": "itemOpusStyle"
    }

    # 伪造 Referer 仍然是必须的
    current_headers = base_headers.copy()
    current_headers['Referer'] = f'https://space.bilibili.com/{host_mid}/dynamic'

    try:
        response = requests.get(list_api_url, headers=current_headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            print(f"  API返回错误 Code: {data.get('code')}, Msg: {data.get('message')}")
            return None

        items_list = data.get('data', {}).get('items')
        if not items_list:
            print(f"  用户(UID: {host_mid}) 暂无动态。")
            return None

        # Desktop API 返回结构中，pub_ts 依然在 modules.module_author 下，逻辑不用变
        latest_post = max(items_list, key=lambda item: item.get('modules', {}).get('module_author', {}).get('pub_ts', 0))
        
        dynamic_id = latest_post.get('id_str')
        if not dynamic_id:
            return None
        
        # 获取详情
        final_content = get_content_from_detail_api(dynamic_id, current_headers)
        
        if final_content is None:
            return None

        publish_timestamp = latest_post.get('modules', {}).get('module_author', {}).get('pub_ts', 0)
        publish_time_str = datetime.fromtimestamp(publish_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        dynamic_url = f"https://www.bilibili.com/opus/{dynamic_id}"

        return {
            "publish_time": publish_time_str,
            "dynamic_url": dynamic_url,
            "content": final_content
        }

    except Exception as e:
        print(f"  请求异常 (UID: {host_mid}): {e}")
        return None

def main():
    if not SESSDATA:
        print("错误：环境变量 BILI_SESSDATA 未设置！")
        exit(1)

    # 基础 Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Cookie': f'SESSDATA={SESSDATA}',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Origin': 'https://space.bilibili.com',
        'Connection': 'keep-alive'
    }

    all_dynamics_data = {}
    print("🚀 开始获取所有目标用户的最新B站动态 (Desktop API)...")

    for user in TARGET_USERS:
        user_name = user['name']
        user_mid = user['mid']
        print(f"\n--- 正在处理用户: {user_name} (UID: {user_mid}) ---")
        
        dynamic_data = fetch_latest_dynamic_for_user(user_mid, headers)
        
        if dynamic_data:
            all_dynamics_data[user_name] = dynamic_data
            print(f"✅ 成功: {user_name}")
        else:
            print(f"❌ 失败: {user_name}")
        
        # 随机延时
        time.sleep(random.uniform(2, 5))

    if not all_dynamics_data:
        print("\n⚠️ 未获取到数据，请检查 Cookie 是否过期。")
        return

    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(all_dynamics_data, f, ensure_ascii=False, indent=4)
        print(f"\n🎉 完成！已保存至 {OUTPUT_FILENAME}")
    except Exception as e:
        print(f"文件写入错误: {e}")

if __name__ == "__main__":
    main()
