import requests
import json
import re
import sys

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
    
    # 提取需要的字段
    weather_data = {
        "publisher": data.get('publisher', '孙培迪'),
        "forecast": data.get('forecst', '既然下雨不可避免，下雨时间从夯到拉（夯-顶尖-人上人-NPC-拉完了）你们会怎么排名？上班通勤时间，下班通勤时间，周末，节假日，上班时间，晚上睡觉时间，中午吃饭时间……（备注：从夯到拉是网络上一种很新的排序分享方式，“夯”代表着强大、厉害，“拉”则是拉胯、低级的意思。“从夯到拉”的排序之间，还有几个细分等级，分别是顶级、人上人、NPC（人机，也就是中规中矩））'),
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
