# get_icon_weather.py (v5.0 - Grid Fetch Version)

import requests
import json
import time

def get_weather_data():
    """
    从 Open-Meteo API 获取一个区域内多个点(网格)的天气数据，
    并将所有数据整合后保存到单一的 iconweather.json 文件中。
    """
    
    # 步骤 1: 定义您的“虚拟气象网格”
    # Key 是点名, Value 是经纬度
    grid_points = {
        'center': {'lat': 23.13, 'lon': 113.26}, # 广州市中心
        'north':  {'lat': 23.40, 'lon': 113.22}, # 北部 (花都)
        'south':  {'lat': 22.78, 'lon': 113.53}, # 南部 (南沙)
        'east':   {'lat': 23.29, 'lon': 113.82}, # 东部 (增城)
        'west':   {'lat': 23.17, 'lon': 112.89}  # 西部 (佛山三水)
    }
    
    # 用于构建API URL的通用参数
    base_url = "https://api.open-meteo.com/v1/forecast"
    common_params = "&hourly=precipitation,wind_gusts_10m,cape&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Asia/Shanghai&models=ecmwf_ifs025,gfs_global,icon_global"
    
    # 用于存储所有网格点数据的字典
    all_grid_data = {}
    
    print("开始获取区域网格天气数据...")

    # 步骤 2: 循环获取每个点的数据
    for name, coords in grid_points.items():
        # 构建当前点的特定URL
        url = f"{base_url}?latitude={coords['lat']}&longitude={coords['lon']}{common_params}"
        
        print(f"正在获取点 '{name}' 的数据 (Lat: {coords['lat']}, Lon: {coords['lon']})...")
        
        try:
            # 使用会话以可能提高性能
            with requests.Session() as session:
                response = session.get(url, timeout=30) # 设置30秒超时
                response.raise_for_status()
                data = response.json()
                
                # 将获取到的数据存入主字典，以点名为键
                all_grid_data[name] = data
                print(f"成功获取点 '{name}' 的数据。")

        except requests.exceptions.RequestException as e:
            print(f"错误: 请求点 '{name}' 的 API 时发生网络错误: {e}")
            # 如果任何一个点失败，则整个任务失败
            return False
        except json.JSONDecodeError:
            print(f"错误: 解析点 '{name}' 返回的 JSON 数据时发生错误。")
            return False
        
        # 在请求之间短暂暂停，避免对API造成过大压力
        time.sleep(1)

    # 步骤 3: 将整合后的数据写入文件
    try:
        with open("iconweather.json", "w", encoding="utf-8") as f:
            json.dump(all_grid_data, f, ensure_ascii=False, indent=4)
        
        print("\n所有网格点天气数据已成功整合并保存到 iconweather.json")
        return True
        
    except Exception as e:
        print(f"\n错误: 写入最终 JSON 文件时发生错误: {e}")
        return False

if __name__ == "__main__":
    if not get_weather_data():
        # 如果函数返回 False (即发生错误)，则以非零状态码退出，
        # 这将使 GitHub Actions 工作流标记为失败。
        exit(1)
