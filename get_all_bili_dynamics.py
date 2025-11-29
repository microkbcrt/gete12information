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
    从详情API获取内容。
    注意：详情API对Referer要求较宽泛，但为了保险起见，建议保持通用Headers。
    """
    detail_api_url = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail"
    params = {"dynamic_id": dynamic_id}
    
    try:
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

            # 4. 备用
            if dynamic_text:
                 return dynamic_text.strip()

            print(f"  警告：未找到有效文本 (ID: {dynamic_id})。")
            return None
        else:
            print(f"  [详情API错误] Code: {data.get('code')}, Message: {data.get('message', '无')}")
            return None
            
    except Exception as e:
        print(f"  [详情API异常] {e}")
        return None

def fetch_latest_dynamic_for_user(host_mid, base_headers):
    """
    修复核心：为每个请求构造特定的 Headers，特别是 Referer
    """
    list_api_url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={host_mid}"

    # --- 【关键修复】 ---
    # 必须为每个用户伪造从其个人空间发起的请求
    current_headers = base_headers.copy()
    current_headers['Referer'] = f'https://space.bilibili.com/{host_mid}/dynamic'
    # ------------------

    try:
        response = requests.get(list_api_url, headers=current_headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            print(f"  列表API返回错误！ Code: {data.get('code')}, Msg: {data.get('message')}")
            # 如果是 -352 或 412，说明风控依然很严，可能需要更换IP或Cookie
            return None

        items_list = data.get('data', {}).get('items')
        if not items_list:
            print(f"  用户(UID: {host_mid}) 暂无动态。")
            return None

        latest_post = max(items_list, key=lambda item: item.get('modules', {}).get('module_author', {}).get('pub_ts', 0))
        
        dynamic_id = latest_post.get('id_str')
        if not dynamic_id:
            print("  错误：无法提取 'id_str'。")
            return None
        
        # 获取详情时可以使用通用的 Referer 或者带上动态ID的 Referer
        detail_headers = base_headers.copy()
        detail_headers['Referer'] = f'https://www.bilibili.com/opus/{dynamic_id}'
        
        final_content = get_content_from_detail_api(dynamic_id, detail_headers)
        
        if final_content is None:
            return None

        publish_timestamp = latest_post.get('modules', {}).get('module_author', {}).get('pub_ts', 0)
        publish_time_str = datetime.fromtimestamp(publish_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        dynamic_url = f"https://www.bilibili.com/opus/{dynamic_id}"

        final_data = {
            "publish_time": publish_time_str,
            "dynamic_url": dynamic_url,
            "content": final_content
        }
        return final_data

    except Exception as e:
        print(f"  请求异常 (UID: {host_mid}): {e}")
        return None

def main():
    if not SESSDATA:
        print("错误：环境变量 BILI_SESSDATA 未设置！")
        exit(1)

    # --- 【Headers 增强】 ---
    # 模拟更真实的浏览器请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': f'SESSDATA={SESSDATA}',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://space.bilibili.com',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }

    all_dynamics_data = {}
    print("🚀 开始获取所有目标用户的最新B站动态...")

    for user in TARGET_USERS:
        user_name = user['name']
        user_mid = user['mid']
        print(f"\n--- 正在处理用户: {user_name} (UID: {user_mid}) ---")
        
        # 传入基础 headers，函数内部会根据 uid 修改 Referer
        dynamic_data = fetch_latest_dynamic_for_user(user_mid, headers)
        
        if dynamic_data:
            all_dynamics_data[user_name] = dynamic_data
            print(f"✅ 成功获取到 '{user_name}' 的最新动态。")
        else:
            print(f"❌ 未能获取到 '{user_name}' 的有效动态，已跳过。")
        
        # 稍微增加延时，避免触发频率限制
        sleep_time = random.uniform(2, 4)
        time.sleep(sleep_time) 

    if not all_dynamics_data:
        print("\n⚠️ 本次运行未能获取到任何用户的动态。")
        return

    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(all_dynamics_data, f, ensure_ascii=False, indent=4)
        print(f"\n\n🎉 任务完成！结果已保存至: {OUTPUT_FILENAME}")
    except Exception as e:
        print(f"\n\n🚨 文件写入错误: {e}")

if __name__ == "__main__":
    main()
