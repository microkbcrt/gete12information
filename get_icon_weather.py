# ==========================================================
# 气象数据获取与智能分析一体化脚本 (v6.1 - 移除GFS源)
#
# 功能:
# 1. 从API获取多个网格点的原始天气数据 (ECMWF, ICON模型)。
# 2. 将原始数据保存到 iconrawweather.json。
# 3. 对原始数据进行智能分析，生成每日摘要。
# 4. 将分析结果保存到 iconweather.json 和 iconweather.js。
# ==========================================================

import requests
import json
import time
import sys
from collections import Counter

# ==========================================================
# 阶段一: 数据获取模块
# ==========================================================
def get_weather_data():
    """
    从 Open-Meteo API 获取一个区域内多个点(网格)的天气数据。
    成功时返回所有点的原始数据字典，失败时返回 None。
    """
    grid_points = {
        'center': {'lat': 23.13, 'lon': 113.26}, # 广州市中心
        'north':  {'lat': 23.40, 'lon': 113.22}, # 北部 (花都)
        'south':  {'lat': 22.78, 'lon': 113.53}, # 南部 (南沙)
        'east':   {'lat': 23.29, 'lon': 113.82}, # 东部 (增城)
        'west':   {'lat': 23.17, 'lon': 112.89}  # 西部 (佛山三水)
    }
    
    base_url = "https://api.open-meteo.com/v1/forecast"
    # 【修改点 1】: 从 models 参数中移除 gfs_global
    common_params = "&hourly=precipitation,wind_gusts_10m,cape&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Asia/Shanghai&models=ecmwf_ifs025,icon_global"
    
    all_grid_data = {}
    
    print("--- 阶段 1: 开始获取区域网格天气数据 (模型: ECMWF, ICON) ---")

    for name, coords in grid_points.items():
        url = f"{base_url}?latitude={coords['lat']}&longitude={coords['lon']}{common_params}"
        print(f"正在获取点 '{name}' 的数据 (Lat: {coords['lat']}, Lon: {coords['lon']})...")
        
        try:
            with requests.Session() as session:
                response = session.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                all_grid_data[name] = data
                print(f"成功获取点 '{name}' 的数据。")
        except requests.exceptions.RequestException as e:
            print(f"错误: 请求点 '{name}' 的 API 时发生网络错误: {e}")
            return None # 返回 None 表示失败
        except json.JSONDecodeError:
            print(f"错误: 解析点 '{name}' 返回的 JSON 数据时发生错误。")
            return None
        
        time.sleep(1)

    try:
        with open("iconrawweather.json", "w", encoding="utf-8") as f:
            json.dump(all_grid_data, f, ensure_ascii=False, indent=4)
        print("\n所有网格点的原始天气数据已成功保存到 iconrawweather.json")
        return all_grid_data # 返回获取到的数据以供下一步分析
    except IOError as e:
        print(f"\n错误: 写入原始数据文件 iconrawweather.json 时发生错误: {e}")
        return None

# ==========================================================
# 阶段二: 数据分析模块 (这部分逻辑不变, 仅在调用处修改模型列表)
# ==========================================================

def get_precip_level(mm):
    """根据降水量(mm)返回降水等级和名称。"""
    if mm < 0.1:  return {'level': 0, 'name': '无雨'}
    if mm < 10:   return {'level': 1, 'name': '小雨'}
    if mm < 25:   return {'level': 2, 'name': '中雨'}
    if mm < 50:   return {'level': 3, 'name': '大雨'}
    if mm < 100:  return {'level': 4, 'name': '暴雨'}
    if mm < 250:  return {'level': 5, 'name': '大暴雨'}
    return {'level': 6, 'name': '特大暴雨'}

def generate_area_conclusion(agg_data):
    """基于聚合后的数据，生成区域的最终天气结论。"""
    if not agg_data.get('precipitations'):
        return {'description': '数据不足', 'icon': 'unknown.png', 'warning': '', 'wmo_code': 0}
    
    precipitations = sorted(agg_data['precipitations'])
    max_precip = precipitations[-1]
    max_level = get_precip_level(max_precip)
    max_gust_kmh = max(agg_data['max_gusts']) if agg_data.get('max_gusts') else 0
    max_cape = max(agg_data['max_capes']) if agg_data.get('max_capes') else 0

    rainy_points = [p for p in precipitations if p >= 0.5]
    coverage_percent = (len(rainy_points) / len(precipitations)) * 100 if precipitations else 0
    is_thunderstorm = max_cape > 700 and max_level['level'] > 0
    
    avg_rainy_points = sum(rainy_points) / len(rainy_points) if rainy_points else 0
    main_level = get_precip_level(avg_rainy_points)

    base_sky_condition = "多云"
    if agg_data.get('wmo_codes'):
        wmo_counts = Counter(agg_data['wmo_codes'])
        total_wmo = len(agg_data['wmo_codes'])
        clear_count = wmo_counts.get(0, 0)
        few_clouds_count = wmo_counts.get(1, 0) + wmo_counts.get(2, 0)
        overcast_count = wmo_counts.get(3, 0)
        
        if (clear_count + few_clouds_count + overcast_count) / total_wmo > 0.6:
            if (clear_count + few_clouds_count) / total_wmo >= 0.6: base_sky_condition = "多云间晴"
            elif (few_clouds_count / total_wmo) >= 0.3 and (overcast_count / total_wmo) >= 0.3: base_sky_condition = "多云到阴天"
            elif overcast_count / total_wmo >= 0.5: base_sky_condition = "阴天"
        else:
            if coverage_percent > 70 and main_level['level'] >= 3: base_sky_condition = "阴天"
            elif coverage_percent > 40 and main_level['level'] >= 2: base_sky_condition = "多云到阴天"
            elif coverage_percent < 20: base_sky_condition = "多云间晴"

    precip_phrase = ""
    if coverage_percent > 15 and main_level['level'] > 0:
        scope_word = "有分散" if coverage_percent < 40 else "有"
        main_precip_name = main_level['name']
        if is_thunderstorm and main_level['level'] <= 1:
            precip_phrase = scope_word + "雷阵雨"
            if max_level['level'] > main_level['level'] + 1: precip_phrase += "局部" + max_level['name']
        else:
            if max_level['level'] <= main_level['level']: precip_phrase = scope_word + main_precip_name
            elif max_level['level'] == main_level['level'] + 1: precip_phrase = scope_word + main_precip_name + "到" + max_level['name']
            else: precip_phrase = scope_word + main_precip_name + "局部" + max_level['name']

    final_desc = base_sky_condition
    if precip_phrase:
        if is_thunderstorm and main_level['level'] >= 2:
            precip_phrase = precip_phrase.replace("中雨", "中雷雨")
        final_desc += "，" + precip_phrase
    
    icon = "01.png"; wmo_code = 1
    if not precip_phrase:
        if '晴' in final_desc: icon = "00.png"; wmo_code = 1
        if final_desc == "晴": wmo_code = 0
        if '阴' in final_desc: icon = "02.png"; wmo_code = 3
    else:
        if is_thunderstorm:
            if coverage_percent < 40: icon = "03.png"; wmo_code = 95
            elif max_level['level'] >= 4: icon = "23.png"; wmo_code = 96
            else: icon = "04.png"; wmo_code = 95
        else:
            if max_level['level'] >= 4: icon = "13.png"; wmo_code = 65
            elif max_level['level'] >= 3: icon = "13.png"; wmo_code = 63
            elif max_level['level'] >= 2: icon = "19.png"; wmo_code = 61
            else: icon = "07.png"; wmo_code = 53

    warnings = []
    if is_thunderstorm and precip_phrase: warnings.append("雷电")
    if (max_gust_kmh / 3.6) >= 13.9: warnings.append("大风")
    warning = "提醒: 可能伴有" + "和".join(warnings) if warnings else ""

    return {'description': final_desc, 'icon': icon, 'warning': warning, 'wmo_code': wmo_code}


def analyze_area_weather_data(all_points_data):
    """分析所有网格点的天气数据。"""
    print("\n--- 阶段 2: 开始分析聚合后的天气数据 ---")
    if not all_points_data:
        raise ValueError("没有任何网格点数据可供分析.")
    
    first_point_key = list(all_points_data.keys())[0]
    days_count = len(all_points_data[first_point_key]['daily']['time'])
    analyzed_results = []
    # 【修改点 2】: 从分析用的模型列表中移除 gfs_global
    models = ['ecmwf_ifs025', 'icon_global']

    for i in range(days_count):
        date = all_points_data[first_point_key]['daily']['time'][i]
        daily_aggregated_data = {
            'precipitations': [], 'max_gusts': [], 'max_capes': [],
            'wmo_codes': [], 'max_temps': [], 'min_temps': []
        }

        for point_data in all_points_data.values():
            avg_max_temp_point, avg_min_temp_point, model_count = 0, 0, 0
            for model in models:
                if f"temperature_2m_max_{model}" in point_data['daily'] and i < len(point_data['daily'][f"temperature_2m_max_{model}"]):
                    avg_max_temp_point += point_data['daily'][f"temperature_2m_max_{model}"][i]
                    avg_min_temp_point += point_data['daily'][f"temperature_2m_min_{model}"][i]
                    model_count += 1
            if model_count > 0:
                daily_aggregated_data['max_temps'].append(avg_max_temp_point / model_count)
                daily_aggregated_data['min_temps'].append(avg_min_temp_point / model_count)

            for model in models:
                if f"precipitation_{model}" in point_data.get('hourly', {}):
                    daily_aggregated_data['precipitations'].append(sum(point_data['hourly'][f"precipitation_{model}"][i*24:(i+1)*24]))
                if f"wind_gusts_10m_{model}" in point_data.get('hourly', {}):
                    gusts = point_data['hourly'][f"wind_gusts_10m_{model}"][i*24:(i+1)*24]
                    if gusts: daily_aggregated_data['max_gusts'].append(max(gusts))
                if f"cape_{model}" in point_data.get('hourly', {}):
                    capes = point_data['hourly'][f"cape_{model}"][i*24:(i+1)*24]
                    if capes: daily_aggregated_data['max_capes'].append(max(capes))
                if f"weather_code_{model}" in point_data['daily'] and i < len(point_data['daily'][f"weather_code_{model}"]):
                    daily_aggregated_data['wmo_codes'].append(point_data['daily'][f"weather_code_{model}"][i])
        
        final_analysis = generate_area_conclusion(daily_aggregated_data)
        avg_max_temp = round(sum(daily_aggregated_data['max_temps']) / len(daily_aggregated_data['max_temps'])) if daily_aggregated_data['max_temps'] else None
        avg_min_temp = round(sum(daily_aggregated_data['min_temps']) / len(daily_aggregated_data['min_temps'])) if daily_aggregated_data['min_temps'] else None
        
        analyzed_results.append({
            'time': date, 
            'temperature_2m_max': avg_max_temp, 
            'temperature_2m_min': avg_min_temp,
            'weather_desc': final_analysis['description'], 
            'weather_icon': final_analysis['icon'],
            'warning_text': final_analysis['warning'], 
            'weather_code': final_analysis['wmo_code']
        })
    print("数据分析完成。")
    return {'daily': analyzed_results}

# ==========================================================
# 主执行流程
# ==========================================================
if __name__ == "__main__":
    # 步骤 1: 获取原始数据
    raw_weather_data = get_weather_data()
    
    if not raw_weather_data:
        print("\n获取原始数据失败，脚本终止。")
        sys.exit(1) # 使用非零退出码，以便 GitHub Actions 识别失败

    # 步骤 2: 分析数据并保存结果
    try:
        analyzed_data = analyze_area_weather_data(raw_weather_data)
        
        print("\n--- 阶段 3: 开始保存分析结果 ---")
        js_file_path = 'iconweather.js'
        json_file_path = 'iconweather.json'
        
        js_content = f"var iconWeatherData = {json.dumps(analyzed_data, ensure_ascii=False, indent=4)};"
        
        with open(js_file_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"成功保存分析结果到 {js_file_path}")
        
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(analyzed_data, f, ensure_ascii=False, indent=4)
        print(f"成功保存分析结果到 {json_file_path}")

        print("\n所有任务成功完成！")

    except Exception as e:
        print(f"\n错误: 在分析数据或保存结果时发生严重错误: {e}")
        sys.exit(1)
