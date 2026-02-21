import requests
import json
import sys

def fetch_rebang_xiaohongshu():
    # API 端点（基于链接内容提供的URL）
    api_url = "https://60s.viki.moe/v2/rednote"
    file_path = "xiaohongshurank.txt"

    try:
        print("正在请求API数据...")
        # 发送GET请求，设置超时时间
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()  # 如果HTTP状态码不是200，抛出异常

        # 解析JSON响应
        result = response.json()
        
        # 检查API返回状态
        if result.get("code") != 200:
            error_msg = result.get("message", "API返回未知错误")
            print(f"❌ API请求失败: {error_msg}")
            sys.exit(1)
        
        # 提取data数组
        data_list = result.get("data", [])
        if not data_list:
            print("❌ 未找到热搜数据")
            return

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            count = 0
            for item in data_list:
                title = item.get("title")
                if title:
                    f.write(title + "\n")
                    count += 1
            print(f"✅ 成功获取 {count} 条小红书热搜，已保存至 {file_path}")

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_rebang_xiaohongshu()
