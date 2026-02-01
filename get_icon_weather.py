import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import re

# ========== 天气描述规范化规则 ==========
# 注意：必须严格按照顺序，先处理"局部多云"再处理"多云"，且只替换一次
def normalize_weather_desc(desc):
    """
    规范化天气描述（精确匹配，只替换一次）
    - 原本是"局部多云" → 替换为"多云"（不再继续替换）
    - 原本是"多云"（且不是由局部多云替换而来）→ 替换为"阴天"
    """
    # 先检查"局部多云"（大关键词优先）
    if '局部多云' in desc:
        # 只替换第一个出现的"局部多云"，替换后立即返回，避免重复替换
        return desc.replace('局部多云', '多云', 1)
    # 再检查"多云"（小关键词）
    elif '多云' in desc:
        # 只替换第一个出现的"多云"
        return desc.replace('多云', '阴天', 1)
    return desc

# ========== 天气图标映射规则 ==========
# 顺序至关重要：先匹配大关键词（如大雨），再匹配小关键词（如雨）
WEATHER_ICON_MAP = [
    ('大雨', '14.png', 4),      # 大雨 -> 14.png
    ('雷阵雨', '04.png', 5),    # 雷阵雨 -> 04.png
    ('雷雨', '23.png', 6),      # 雷雨 -> 23.png
    ('晴朗', '00.png', 1),      # 晴朗 -> 00.png
    ('多云', '01.png', 2),      # 多云 -> 01.png（注意：规范化后"局部多云"会变成"多云"）
    ('阴天', '02.png', 3),      # 阴天 -> 02.png（注意：规范化后"多云"会变成"阴天"）
    ('雨', '19.png', 4)         # 雨 -> 19.png（最后匹配，避免被大雨等覆盖）
]

def fetch_weather_data(url):
    """
    从 weather.com 获取天气预报 HTML 内容
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"❌ 获取网页内容时出错: {e}")
        return None

def get_weather_icon_and_code(weather_desc_raw):
    """
    根据原始天气描述获取图标和代码
    1. 先规范化描述（但不改变原始描述的替换逻辑）
    2. 按顺序匹配关键词（大关键词优先）
    """
    # 使用原始描述进行规范化（内部已处理单次替换逻辑）
    normalized_desc = normalize_weather_desc(weather_desc_raw)
    
    # 按顺序匹配图标（大关键词优先）
    for keyword, icon, code in WEATHER_ICON_MAP:
        if keyword in normalized_desc:
            return icon, code
    
    # 默认返回晴朗图标
    return '00.png', 1

def parse_date_from_text(date_text):
    """
    从 "今天白天"、"明天晚上"、"周一 02" 等文本中解析日期
    
    返回: "2026-02-01" 格式的日期字符串
    """
    today = datetime.now()
    
    # 处理"今天"
    if '今天' in date_text:
        return today.strftime('%Y-%m-%d')
    
    # 处理"明天"
    if '明天' in date_text:
        tomorrow = today + timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d')
    
    # 处理"周一 02"等带数字的格式
    match = re.search(r'(\d{1,2})', date_text)
    if match:
        day = int(match.group(1))
        current_day = today.day
        current_month = today.month
        current_year = today.year
        
        # 如果提取的日期小于当前日期，说明是下个月
        if day < current_day:
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
        
        return f"{current_year:04d}-{current_month:02d}-{day:02d}"
    
    # 无法解析时返回今天
    return today.strftime('%Y-%m-%d')

def parse_temperature(temp_str):
    """
    从 "18°/11°" 这样的字符串中解析最高温和最低温
    
    返回: (max_temp, min_temp) 元组
    """
    # 移除度数符号
    temp_str = temp_str.replace('°', '')
    
    # 匹配温度数字
    temps = re.findall(r'\d+', temp_str)
    
    if len(temps) >= 2:
        return int(temps[0]), int(temps[1])
    elif len(temps) == 1:
        temp = int(temps[0])
        return temp, temp
    else:
        return 0, 0

def parse_weather_forecast(soup, days=10):
    """
    解析天气预报，返回符合 iconweather.json 格式的数据
    """
    # 查找天气预报容器
    forecast_container = soup.find('div', class_='DailyForecast--DisclosureList--xG4Oa')
    
    if not forecast_container:
        print("❌ 未找到天气预报容器，请检查网页结构是否已更改")
        return None
    
    # 查找所有天气预报详情卡片
    forecast_days = forecast_container.find_all(
        'details', 
        class_='DaypartDetails--DayPartDetail--n5F8Y'
    )
    
    if not forecast_days:
        print("❌ 未找到天气预报数据，请检查网页结构是否已更改")
        return None
    
    daily_data = []
    
    # 遍历前 N 天的预报
    for i, day in enumerate(forecast_days[:days]):
        try:
            # 1. 提取日期
            date_elem = day.find('h2', attrs={'data-testid': 'daypartName'})
            date_text = date_elem.get_text(strip=True) if date_elem else "未知日期"
            date = parse_date_from_text(date_text)
            
            # 2. 提取天气状况（原始描述）
            weather_elem = day.find('span', class_='DetailsSummary--wxPhrase--nhYpy')
            weather_desc_raw = weather_elem.get_text(strip=True) if weather_elem else "晴朗"
            
            # 规范化天气描述（单次替换）
            weather_desc = normalize_weather_desc(weather_desc_raw)
            
            # 获取图标和代码（基于规范化后的描述匹配）
            weather_icon, weather_code = get_weather_icon_and_code(weather_desc_raw)
            
            # 3. 提取温度
            temp_div = day.find('div', attrs={'data-testid': 'detailsTemperature'})
            if temp_div:
                high_temp_elem = temp_div.find('span', class_='DetailsSummary--highTempValue--VHKaO')
                low_temp_elem = temp_div.find('span', class_='DetailsSummary--lowTempValue--ogrzb')
                
                high = high_temp_elem.get_text(strip=True) if high_temp_elem else "0°"
                low = low_temp_elem.get_text(strip=True) if low_temp_elem else "0°"
                
                temperature_2m_max, temperature_2m_min = parse_temperature(f"{high}/{low}")
            else:
                temperature_2m_max, temperature_2m_min = 0, 0
            
            # 4. 构建每日数据
            daily_item = {
                "time": date,
                "temperature_2m_max": temperature_2m_max,
                "temperature_2m_min": temperature_2m_min,
                "weather_desc": weather_desc,  # 存储规范化后的描述
                "weather_icon": weather_icon,
                "warning_text": "",
                "weather_code": weather_code
            }
            
            daily_data.append(daily_item)
            
        except Exception as e:
            print(f"⚠️ 解析第 {i+1} 天数据时出错: {e}")
            continue
    
    return {"daily": daily_data}

def export_to_json(data, filename='iconweather.json'):
    """
    导出为 JSON 文件
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✓ 已导出到 {filename}")
        
        # 打印预览（前3天）
        print("\n📊 JSON 预览（前3天）:")
        preview = {"daily": data['daily'][:3]} if data and 'daily' in data else data
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"❌ 导出 JSON 时出错: {e}")

def print_summary(data):
    """
    打印天气数据摘要
    """
    if not data or 'daily' not in data:
        print("❌ 没有可用的天气数据")
        return
    
    print(f"\n{'='*70}")
    print(f"🌤️  天气预报摘要 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"{'='*70}")
    
    for item in data['daily'][:5]:  # 只显示前5天摘要
        print(f"{item['time']} | {item['weather_desc']:10s} | "
              f"🌡️ {item['temperature_2m_max']:2d}°/{item['temperature_2m_min']:2d}° | "
              f"🖼️ {item['weather_icon']:6s} | "
              f"#{item['weather_code']}")
    
    if len(data['daily']) > 5:
        print(f"... 共 {len(data['daily'])} 天预报，完整数据请查看 iconweather.json")
    print(f"{'='*70}\n")

# ========== 主程序 ==========
if __name__ == "__main__":
    # weather.com 的广州10天预报页面 URL（已清理末尾空格）
    url = "https://weather.com/zh-CN/weather/tenday/l/fddd34a41b7ab44789a7a1676b33735bc5c802d4a364d78438a0cdf51b881782"
    
    print("=" * 70)
    print("⏳ 正在获取广州天气数据，请稍候...")
    print("=" * 70)
    
    # 获取并解析网页
    soup = fetch_weather_data(url)
    
    if soup:
        # 解析天气数据
        weather_data = parse_weather_forecast(soup, days=10)
        
        if weather_data and weather_data.get('daily'):
            # 打印摘要
            print_summary(weather_data)
            
            # 导出为 JSON
            export_to_json(weather_data, 'iconweather.json')
            
            print("\n✅ 天气数据处理完成！")
            print("💡 规范化规则说明:")
            print("   • '局部多云' → '多云'（仅替换一次，不再继续替换为阴天）")
            print("   • '多云' → '阴天'（仅当原始描述为'多云'时替换）")
            print("   • 图标匹配顺序：大雨 > 雷阵雨 > 雷雨 > 晴朗 > 多云 > 阴天 > 雨")
        else:
            print("❌ 未能解析天气数据")
    else:
        print("❌ 无法获取网页内容，请检查网络连接或 URL")
