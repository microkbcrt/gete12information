import requests
import json

def fetch_and_save_zhihu_rank():
    # 目标API地址
    url = "https://api.pearktrue.cn/api/dailyhot/?title=%E7%9F%A5%E4%B9%8E"
    
    # 保存的文件名
    file_path = "zhihurank.txt"
    
    # 设置请求头，伪装成浏览器（虽然这个API通常不严格校验，但加上更保险）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print(f"正在请求: {url} ...")
        # 1. 发送请求
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # 检查HTTP状态码是否为200

        # 2. 解析JSON
        result = response.json()
        
        # 检查API返回状态码
        if result.get("code") != 200:
            print(f"API返回错误信息: {result.get('msg')}")
            return

        # 3. 提取 data 列表
        hot_list = result.get("data", [])
        
        if not hot_list:
            print("未获取到热搜数据列表。")
            return

        # 4. 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            count = 0
            for item in hot_list:
                # 提取 title 字段
                title = item.get("title")
                # 确保标题存在且不为空
                if title:
                    f.write(title + "\n")
                    count += 1
        
        print(f"成功获取 {count} 条知乎热榜标题，已保存至 {file_path}")

    except requests.exceptions.RequestException as e:
        print(f"网络请求出错: {e}")
    except json.JSONDecodeError:
        print("JSON解析失败，API可能返回了非JSON格式的数据。")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    fetch_and_save_zhihu_rank()
