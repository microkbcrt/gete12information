import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import os

# --- 配置区 ---
HOST_MID = "1636034895"
OUTPUT_FILENAME = 'latest_bili_post.json'
SESSDATA = os.environ.get('BILI_SESSDATA')

def scrape_opus_page_content(opus_url, headers):
    """
    增强版抓取函数：如果找不到目标容器，则输出整个HTML页面用于调试。
    """
    print(f"正在抓取动态详情页: {opus_url}")
    try:
        response = requests.get(opus_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # 获取响应的文本内容
        html_content = response.text

        soup = BeautifulSoup(html_content, 'lxml')
        content_div = soup.find('div', class_='opus-module-content')

        if content_div:
            # 找到了，正常返回文本
            print("成功找到 'opus-module-content' 容器。")
            full_text = content_div.get_text(separator='\n', strip=True)
            return full_text
        else:
            # --- 关键的诊断代码 ---
            # 没找到，打印整个HTML页面到日志中
            print("\n" + "="*50)
            print("【诊断信息】未能在页面中找到 'opus-module-content' 容器。")
            print("这很可能是因为B站返回了一个登录页、验证页或错误页。")
            print("以下是GitHub Actions实际抓取到的完整HTML页面内容：")
            print("="*50 + "\n")
            print(html_content) # 打印完整HTML
            print("\n" + "="*50)
            print("【诊断信息结束】请检查上面的HTML内容以确定问题原因。")
            print("="*50 + "\n")
            
            # 仍然返回一个明确的错误信息写入JSON
            return "[抓取错误] 未能找到目标内容容器。请查看Actions日志中的诊断信息。"

    except requests.exceptions.RequestException as e:
        print(f"抓取详情页失败: {e}")
        return f"[网络错误] 无法访问动态详情页: {opus_url}"
    except Exception as e:
        print(f"解析HTML时发生错误: {e}")
        return "[解析错误] 解析详情页HTML时出错。"

def fetch_and_process_dynamics():
    # ... (这部分主函数和之前完全一样，无需修改) ...
    api_url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={HOST_MID}"

    if not SESSDATA:
        print("错误：环境变量 BILI_SESSDATA 未设置！")
        exit(1)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Cookie': f'SESSDATA={SESSDATA}',
        'Referer': f'https://space.bilibili.com/{HOST_MID}/dynamic',
        # 尝试添加更多请求头，让请求看起来更像真实浏览器
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive',
    }

    print(f"第一步：正在通过API获取用户(UID: {HOST_MID})的动态列表...")
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') != 0:
            print(f"API返回错误！ 代码: {data.get('code')}, 信息: {data.get('message', '无')}")
            exit(1)

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
