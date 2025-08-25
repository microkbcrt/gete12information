import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import os  # 导入os库来读取环境变量

# --- 配置区 ---
HOST_MID = "1636034895"
OUTPUT_FILENAME = 'latest_bili_phigros_post.json' # 修改了输出文件名以区分

# 从环境变量中读取SESSDATA，这是在GitHub Actions中使用的最佳实践
# os.environ.get('BILI_SESSDATA') 会尝试读取名为 BILI_SESSDATA 的环境变量
# 如果在本地测试，你可以手动设置这个环境变量，或者临时在这里赋值
SESSDATA = os.environ.get('BILI_SESSDATA')

def scrape_opus_page_content(opus_url, headers):
    # ... (这部分函数和之前完全一样，无需修改) ...
    print(f"正在抓取动态详情页: {opus_url}")
    try:
        response = requests.get(opus_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        content_div = soup.find('div', class_='opus-module-content')
        if content_div:
            full_text = content_div.get_text(separator='\n', strip=True)
            return full_text
        else:
            return "[抓取错误] 在页面中未能找到 'opus-module-content' 容器。"
    except requests.exceptions.RequestException as e:
        print(f"抓取详情页失败: {e}")
        return f"[网络错误] 无法访问动态详情页: {opus_url}"
    except Exception as e:
        print(f"解析HTML时发生错误: {e}")
        return "[解析错误] 解析详情页HTML时出错。"

def fetch_and_process_dynamics():
    api_url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={HOST_MID}"

    # 在脚本开始时就检查SESSDATA是否存在
    if not SESSDATA:
        print("错误：环境变量 BILI_SESSDATA 未设置！请在GitHub Secrets中添加它。")
        # 使用 exit(1) 来使工作流步骤失败，这样更容易发现问题
        exit(1)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Cookie': f'SESSDATA={SESSDATA}',
        'Referer': f'https://space.bilibili.com/{HOST_MID}/dynamic'
    }

    print(f"第一步：正在通过API获取用户(UID: {HOST_MID})的动态列表...")
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') != 0:
            print(f"API返回错误！ 代码: {data.get('code')}, 信息: {data.get('message', '无')}")
            exit(1) # API出错也直接让工作流失败

        items_list = data.get('data', {}).get('items')
        if not items_list:
            print("API返回的数据中未找到动态列表。")
            return

        latest_post = max(items_list, key=lambda item: item.get('modules', {}).get('module_author', {}).get('pub_ts', 0))
        
        dynamic_id = latest_post.get('id_str')
        if not dynamic_id:
            print("错误：无法从最新的动态中提取到 'id_str'。")
            exit(1)

        opus_url = f"https://www.bilibili.com/opus/{dynamic_id}"
        print(f"\n第二步：已找到最新动态ID({dynamic_id})，准备抓取详情页。")
        
        final_content = scrape_opus_page_content(opus_url, headers)
        
        publish_timestamp = latest_post.get('modules', {}).get('module_author', {}).get('pub_ts', 0)
        publish_time_str = datetime.fromtimestamp(publish_timestamp).strftime('%Y-%m-%d %H:%M:%S')

        final_data = {
            "publish_time": publish_time_str,
            "dynamic_url": opus_url,
            "content": final_content
        }

        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)

        print(f"\n🎉 任务完成！详细内容已保存到文件: {OUTPUT_FILENAME}")
        
    except requests.exceptions.RequestException as e:
        print(f"API请求失败: {e}")
        exit(1)
    except Exception as e:
        print(f"发生未知错误: {e}")
        exit(1)

if __name__ == "__main__":
    fetch_and_process_dynamics()
