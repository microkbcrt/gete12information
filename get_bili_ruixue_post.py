import requests
import json
from datetime import datetime
import os

# --- 配置区 ---
HOST_MID = "258614728"
OUTPUT_FILENAME = 'latest_bili_ruixue_post_details.json' # 文件名保持不变
SESSDATA = os.environ.get('BILI_SESSDATA')

def get_content_from_detail_api(dynamic_id, headers):
    """
    从详情API获取内容。如果找不到关键文本字段，则返回 None。
    """
    detail_api_url = "https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail"
    
    params = {
        "dynamic_id": dynamic_id
    }
    
    print(f"正在请求最终版详情API以获取动态({dynamic_id})的完整内容...")
    
    try:
        response = requests.get(detail_api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') == 0 and data.get('data', {}).get('card'):
            card_str = data['data']['card'].get('card')
            card_data = json.loads(card_str)
            
            # --- 【逻辑修改 1】 ---
            # 优先尝试 'item.description'
            description = card_data.get('item', {}).get('description')
            if description is not None:
                print("成功从 'item.description' 字段获取到文本内容。")
                return description.strip()
            
            # 如果上面找不到，再尝试 'dynamic' (适用于视频等)
            dynamic_text = card_data.get('dynamic')
            if dynamic_text is not None:
                 print("成功从 'dynamic' 字段获取到文本内容。")
                 return dynamic_text.strip()

            # 如果两者都找不到，说明是无意义动态，返回 None
            print("警告：在详情API响应中未能找到 'description' 或 'dynamic' 字段。此动态被视为无文本内容，将跳过更新。")
            return None
        else:
            error_msg = f"[详情API错误] Code: {data.get('code')}, Message: {data.get('message', '无')}"
            print(error_msg)
            return None # API出错也返回None，以防止更新
            
    except Exception as e:
        error_msg = f"[严重错误] 处理详情API时发生异常: {e}"
        print(error_msg)
        return None # 任何异常都返回None，确保不执行更新


def fetch_and_process_dynamics():
    """
    主函数：获取动态ID，调用详情API，检查内容后才保存结果。
    """
    list_api_url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={HOST_MID}"

    if not SESSDATA:
        print("错误：环境变量 BILI_SESSDATA 未设置！")
        exit(1)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Cookie': f'SESSDATA={SESSDATA}',
        'Referer': f'https://space.bilibili.com/{HOST_MID}/dynamic'
    }

    print(f"第一步：正在通过列表API获取用户(UID: {HOST_MID})的最新动态ID...")

    try:
        response = requests.get(list_api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            print(f"列表API返回错误！ 代码: {data.get('code')}, 信息: {data.get('message', '无')}")
            exit(1)

        items_list = data.get('data', {}).get('items')
        if not items_list:
            print("列表API返回的数据中未找到动态。")
            return

        latest_post = max(items_list, key=lambda item: item.get('modules', {}).get('module_author', {}).get('pub_ts', 0))
        
        dynamic_id = latest_post.get('id_str')
        if not dynamic_id:
            print("错误：无法从最新的动态中提取到 'id_str'。")
            exit(1)
        
        print(f"\n第二步：已找到最新动态ID({dynamic_id})。")
        
        final_content = get_content_from_detail_api(dynamic_id, headers)
        
        # --- 【逻辑修改 2】 ---
        # 如果 final_content 是 None，说明获取失败或内容无意义，则直接退出
        if final_content is None:
            print("\n因为未能获取到有效的动态文本内容，本次将不更新JSON文件。脚本正常结束。")
            return # 正常退出函数，不执行后续写入操作

        # 只有在获取到有效内容时，才继续执行下面的代码
        publish_timestamp = latest_post.get('modules', {}).get('module_author', {}).get('pub_ts', 0)
        publish_time_str = datetime.fromtimestamp(publish_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        dynamic_url = f"https://www.bilibili.com/opus/{dynamic_id}"

        final_data = {
            "publish_time": publish_time_str,
            "dynamic_url": dynamic_url,
            "content": final_content
        }

        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)

        print(f"\n🎉 任务完成！最准确的动态内容已保存到文件: {OUTPUT_FILENAME}")
        print("\n--- 最终结果 ---")
        print(f"发布时间: {final_data['publish_time']}")
        print(f"动态链接: {final_data['dynamic_url']}")
        print(f"动态内容:\n{final_data['content']}")

    except Exception as e:
        print(f"主函数发生未知错误: {e}")
        exit(1)

if __name__ == "__main__":
    fetch_and_process_dynamics()
