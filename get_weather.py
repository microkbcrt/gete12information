import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_weather_data():
    """获取广州十天天气预报数据，解析后按指定格式保存到文件"""
    url = "http://www.tqyb.com.cn/data/ten/GZFR.HTML"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # 发送HTTP请求
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'  # 明确指定编码为UTF-8
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取标题（处理可能的编码问题）
        title = soup.find('strong', string=lambda text: "未来十天天气" in str(text)).get_text(strip=True)
        
        # 提取过程天气预报（所有包含日期的段落）
        forecast_paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if any(date in text for date in ["6月27日", "6月28日", "7月1日", "7月2-6日"]):
                forecast_paragraphs.append(text)
        
        # 提取应用建议（编号1和2的段落）
        advice_paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text.startswith(("1. ", "2. ")):
                advice_paragraphs.append(text)
        
        # 提取发布单位和时间
        footer = soup.find_all('div', style=lambda s: "text-align:right" in str(s))
        bureau = footer[0].get_text(strip=True) if footer else "广州市气象台"
        time = footer[1].get_text(strip=True) if len(footer) > 1 else ""
        
        # 按指定格式整理内容
        formatted_content = f"{title}\n\n一、过程天气预报\n"
        formatted_content += "\n".join(forecast_paragraphs) + "\n\n"
        formatted_content += "二、气象预报应用建议\n"
        formatted_content += "\n".join(advice_paragraphs) + "\n\n"
        formatted_content += f"{bureau}\n{time}"
        
        # 保存到文件
        with open("tendaysweather.txt", "w", encoding="utf-8") as file:
            file.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            file.write(formatted_content)
            
        print("天气数据已按格式保存到 tendaysweather.txt")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return False
    except Exception as e:
        print(f"解析或保存时出错: {e}")
        return False

if __name__ == "__main__":
    fetch_weather_data()
