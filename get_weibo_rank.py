import requests
import json

def fetch_and_save_weibo_rank():
    """
    从API获取微博热搜数据，提取标题并保存到 weiborank.txt 文件中。
    适配接口：https://uapis.cn/api/v1/misc/hotboard?type=weibo
    输出格式：每行一个标题（保持原格式）
    """
    # 新API地址
    api_url = "https://uapis.cn/api/v1/misc/hotboard?type=weibo"
    # 保存的文件名
    file_path = "weiborank.txt"

    try:
        # 1. 发送HTTP GET请求
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()

        # 2. 解析JSON数据
        result = response.json()

        # 3. 获取数据列表
        # 新接口返回结构：{"type": "weibo", "update_time": "...", "list": [...]}
        hot_list = result.get("list", [])

        if not hot_list:
            print("API返回数据为空，请检查接口状态。")
            return

        # 4. 提取标题并写入TXT文件（保持原输出格式：每行一个标题）
        with open(file_path, "w", encoding="utf-8") as f:
            count = 0
            for item in hot_list:
                # 提取 'title' 字段
                title = item.get("title")
                if title:
                    f.write(title + "\n")
                    count += 1

        print(f"成功获取 {count} 条微博热搜标题并保存到 {file_path}")

    except requests.exceptions.RequestException as e:
        print(f"请求API时发生错误: {e}")
    except json.JSONDecodeError:
        print("解析JSON响应失败，API可能返回了无效的数据。")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    fetch_and_save_weibo_rank()
