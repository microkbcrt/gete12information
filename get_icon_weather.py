# get_icon_weather.py

import requests
import json

def get_weather_data():
    """
    从 Open-Meteo API 获取天气数据并保存到 iconweather.json 文件中。
    """
    # API URL
    url = "https://api.open-meteo.com/v1/forecast?latitude=23.13&longitude=113.26&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=Asia/Shanghai"
    
    try:
        # 发送 GET 请求
        response = requests.get(url)
        # 检查响应状态码，如果不是 200 则抛出异常
        response.raise_for_status()
        
        # 解析 JSON 数据
        data = response.json()
        
        # 将数据写入文件
        with open("iconweather.json", "w", encoding="utf-8") as f:
            # 使用 indent=4 参数使 JSON 文件格式化，更易于阅读
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print("天气数据已成功获取并保存到 iconweather.json")
        
    except requests.exceptions.RequestException as e:
        # 捕获网络请求相关的错误
        print(f"请求 API 时发生错误: {e}")
    except json.JSONDecodeError:
        # 捕获 JSON 解析错误
        print("解析返回的 JSON 数据时发生错误")
    except Exception as e:
        # 捕获其他所有未知错误
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    get_weather_data()
