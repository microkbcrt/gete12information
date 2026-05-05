import requests
import json

def fetch_and_save_netease_music_rank():
    """
    从新 API 获取网易云音乐热榜数据，提取标题并保存到 xiaohongshurank.txt 文件中。
    """
    # 新 API 地址（type=netease-music）
    api_url = "https://uapis.cn/api/v1/misc/hotboard?type=netease-music"
    # 按用户要求保存为指定文件名
    file_path = "xiaohongshurank.txt"

    # 设置请求头，伪装成浏览器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print(f"正在请求: {api_url} ...")
        # 1. 发送 HTTP GET 请求
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()

        # 2. 解析 JSON 数据
        result = response.json()

        # 3. 获取包含热榜列表的 'list' 字段（新 API 统一结构）
        hot_list = result.get("list", [])

        if not hot_list:
            print("未能获取到数据列表，可能是 API 返回为空或结构变更。")
            return

        # 4. 提取标题并写入 TXT 文件
        with open(file_path, "w", encoding="utf-8") as f:
            count = 0
            for item in hot_list:
                # 提取 'title' 字段（歌曲/榜单名称）
                title = item.get("title")
                if title:
                    f.write(title + "\n")
                    count += 1

        print(f"成功获取 {count} 条网易云音乐热榜标题，已保存至 {file_path}")

    except requests.exceptions.RequestException as e:
        print(f"网络请求出错: {e}")
    except json.JSONDecodeError:
        print("JSON 解析失败，API 可能返回了非 JSON 格式的数据。")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    fetch_and_save_netease_music_rank()
