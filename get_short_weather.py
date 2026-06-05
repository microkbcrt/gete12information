import requests
import json
import re
import sys

# 定义固定祝福语
blessing = "画凌烟，上甘泉，自古功名属少年，临近高考，广州市气象台祝各位考生考试顺利，金榜题名，落笔生花，圆梦今夏！"

# 设置响应头为JSON格式
print('Content-Type: application/json')
print()

try:
    # 请求数据
    url = "http://www.tqyb.com.cn/data/shorttime/gz_shorttime.js"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"请求失败: HTTP状态码 {response.status_code}")
    
    # 解析JavaScript变量
    match = re.search(r'var\s+gz_shorttime\s*=\s*(\{.*?\});', response.text, re.DOTALL)
    if not match:
        raise Exception("数据解析失败")
    
    # 解析JSON数据
    data = json.loads(match.group(1))
    
    # 提取原始预报内容，拼接祝福语
    default_forecast = '目前广州市多云多云，花都区出现冰雹，白云区、从化区、黄埔区、增城区出现强雷雨。预计17-20时，我市中北部地区有中到强雷雨，其余地区多云间阴天，局部有阵雨，气温28到32℃，吹轻微的西南风；20-23时，多云间阴天，局部有阵雨，气温26到299℃，吹轻微的西南风。'
    origin_forecast = data.get('forecast', default_forecast)
    final_forecast = origin_forecast + blessing  # 天气+祝福语拼接
    
    # 组装返回数据
    weather_data = {
        "publisher": data.get('publisher', '刘连望帆'),
        "forecast": final_forecast,
        "rtime": data.get('rtime', '刚刚')
    }
    
    # 保存本地副本（可选）
    with open("getshortweather.json", "w", encoding="utf-8") as f:
        json.dump(weather_data, f, ensure_ascii=False, indent=2)
    
    # 输出JSON数据
    print(json.dumps(weather_data, ensure_ascii=False))

except Exception as e:
    # 错误处理
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
