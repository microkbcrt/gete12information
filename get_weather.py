import requests
from datetime import datetime

def fetch_weather_data():
    """获取广州十天天气预报数据并保存到文件"""
    url = "http://www.tqyb.com.cn/data/ten/GZFR.HTML"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # 发送 HTTP 请求
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        
        # 保存内容到文件
        with open("tendaysweather.txt", "w", encoding="utf-8") as file:
            file.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(response.text)
            
        print("天气数据已成功保存到 tendaysweather.txt")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return False
    except Exception as e:
        print(f"发生未知错误: {e}")
        return False

if __name__ == "__main__":
    fetch_weather_data()
