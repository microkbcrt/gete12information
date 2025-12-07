import requests
import json

def fetch_and_save_bilibili_rank():
    """
    从API获取B站热搜数据，提取标题并保存到bilibilirank.txt文件中。
    """
    api_url = "https://api.pearktrue.cn/api/dailyhot/?title=哔哩哔哩"
    file_path = "bilibilirank.txt"

    try:
        # 1. 发送HTTP GET请求
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        # 2. 解析JSON数据
        result = response.json()

        # 3. 获取包含热搜列表的 'data' 字段
        # 注意：该API通常返回结构为 {"code": 200, "msg": "success", "data": [...]}
        hot_list = result.get("data", [])

        if not hot_list:
            print("未能获取到数据列表，可能是API返回为空或结构变更。")
            return

        # 4. 提取标题并写入TXT文件
        with open(file_path, "w", encoding="utf-8") as f:
            count = 0
            for item in hot_list:
                # 提取 'title' 字段，例如 "三国，但全女版"
                title = item.get("title")
                if title:
                    f.write(title + "\n")
                    count += 1

        print(f"成功获取 {count} 条B站热搜标题并保存到 {file_path}")

    except requests.exceptions.RequestException as e:
        print(f"请求API时发生错误: {e}")
    except json.JSONDecodeError:
        print("解析JSON响应失败，API可能返回了无效的数据。")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    fetch_and_save_bilibili_rank()
