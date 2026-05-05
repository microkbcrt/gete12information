import requests
import json

def fetch_and_save_bilibili_rank():
    """
    从新 API 获取 B 站热搜数据，提取标题并保存到 bilibilirank.txt 文件中。
    """
    # 更新为新的 API 地址
    api_url = "https://uapis.cn/api/v1/misc/hotboard?type=bilibili"
    file_path = "bilibilirank.txt"

    try:
        # 1. 发送 HTTP GET 请求
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        # 2. 解析 JSON 数据
        result = response.json()

        # 3. 获取包含热搜列表的 'list' 字段（新 API 结构）
        hot_list = result.get("list", [])

        if not hot_list:
            print("未能获取到数据列表，可能是 API 返回为空或结构变更。")
            return

        # 4. 提取标题并写入 TXT 文件
        with open(file_path, "w", encoding="utf-8") as f:
            count = 0
            for item in hot_list:
                # 提取 'title' 字段
                title = item.get("title")
                if title:
                    f.write(title + "\n")
                    count += 1

        print(f"成功获取 {count} 条 B 站热搜标题并保存到 {file_path}")

    except requests.exceptions.RequestException as e:
        print(f"请求 API 时发生错误：{e}")
    except json.JSONDecodeError:
        print("解析 JSON 响应失败，API 可能返回了无效的数据。")
    except Exception as e:
        print(f"发生未知错误：{e}")

if __name__ == "__main__":
    fetch_and_save_bilibili_rank()
