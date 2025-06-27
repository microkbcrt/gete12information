import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def fetch_weather_data():
    """获取并解析广州天气预报，按指定格式保存"""
    url = "http://www.tqyb.com.cn/data/ten/GZFR.HTML"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取所有文本内容并合并连续空格
        all_text = re.sub(r'\s+', ' ', soup.get_text(strip=False))
        
        # 按标题分割内容（假设标题唯一）
        title = re.search(r'([\u4e00-\u9fa5]+未来十天天气趋势预报?和?建议?)', all_text)
        title = title.group(1) if title else "广州市未来十天天气趋势预报和建议"
        
        # 提取过程天气预报（基于"一、过程天气预报"后的内容）
        forecast_section = re.search(r'一、过程天气预报(.*?)二、气象预报应用建议', all_text, re.DOTALL)
        forecast_content = forecast_section.group(1).strip() if forecast_section else ""
        
        # 提取应用建议（基于"二、气象预报应用建议"后的内容）
        advice_section = re.search(r'二、气象预报应用建议(.*?)[广州市气象台]', all_text, re.DOTALL)
        advice_content = advice_section.group(1).strip() if advice_section else ""
        
        # 提取发布信息
        bureau_section = re.search(r'([广州市气象台]+)\s*(\d{4}年\d{1,2}月\d{1,2}日\d{1,2}时)', all_text)
        bureau = bureau_section.group(1) if bureau_section else "广州市气象台"
        time = bureau_section.group(2) if bureau_section else "2025年06月27日11时"
        
        # 整理格式（处理可能的空行）
        formatted_content = f"{title}\n\n一、过程天气预报\n{forecast_content}\n\n"
        formatted_content += "二、气象预报应用建议\n{advice_content}\n\n{}\n{}".format(
            advice_content, bureau, time)
        
        # 保存到文件
        with open("tendaysweather.txt", "w", encoding="utf-8") as file:
            file.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            file.write(formatted_content.replace("  ", " "))  # 清理多余空格
            
        print("天气数据已优化保存")
        return True
        
    except Exception as e:
        print(f"处理出错: {e}")
        return False

if __name__ == "__main__":
    fetch_weather_data()
