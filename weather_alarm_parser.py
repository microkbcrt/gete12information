import requests
import json
import re

def fetch_and_parse_alarm_data():
    # 1. 使用新的、稳定的API URL
    # 我们移除了 callback, _, jsoncallback 等动态参数
    url = "https://wxc.gd121.cn/gdecloud/servlet/servletcityweatherall4?DISTRICTCODE=440100"
    
    # 添加请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://wxc.gd121.cn/'
    }

    try:
        # 发送HTTP请求获取内容
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        print(f"成功获取网页内容，长度: {len(response.text)} 字节")
    except requests.exceptions.RequestException as e:
        print(f"无法获取网页内容，请检查链接或网络状态。错误: {e}")
        return
    
    # 2. 提取JSONP回调中的JSON数据
    # 新的格式是 callback({...})，而不是变量赋值
    match = re.search(r'^\w+\((.*)\)$', response.text, re.DOTALL)
    if not match:
        print("无法从JSONP响应中解析出JSON内容，请检查网页格式。")
        return
    
    json_data_str = match.group(1)
    print("成功从JSONP响应中提取JSON数据")
    
    try:
        # 将JSON字符串转换为Python字典
        data = json.loads(json_data_str)
        print("成功解析JSON数据")
    except json.JSONDecodeError as e:
        print(f"JSON解析失败，请检查数据格式。错误: {e}")
        return
    
    # 目标区域名称
    target_area = "荔湾"
    # 初始化目标区域预警信息列表
    area_alarms = []
    
    # 3. 遍历新的数据结构以查找预警
    try:
        # 新的预警数据在 'rows' 列表的第一个元素的 'yjrows' 和 'yjrowsV9' 键中
        # 我们将两个列表合并，以防预警信息分散在两处
        all_alarms = data.get('rows', [{}])[0].get('yjrows', [])
        all_alarms.extend(data.get('rows', [{}])[0].get('yjrowsV9', []))
        
        if not all_alarms:
            print("警告: 在返回的数据中未找到预警信息列表。")
    except (IndexError, KeyError) as e:
        print(f"解析预警列表失败，JSON结构可能已变更。错误: {e}")
        all_alarms = []

    # 遍历所有预警信息
    for alarm_item in all_alarms:
        if not isinstance(alarm_item, dict):
            continue
            
        # 检查区域名称是否匹配 (新的字段是 'areacodename')
        if alarm_item.get('areacodename') == target_area:
            
            # 4. 提取信息并映射到旧的格式
            alarm_type_name = alarm_item.get('yjtitle', '未知预警类型')
            
            # 新数据源将含义和防御措施合并在 'content' 字段中
            content = alarm_item.get('content', '无详细信息')
            meaning = content
            guidelines = content
            
            # 添加到结果列表，保持原有的字典结构
            area_alarms.append({
                "area": target_area,
                "alarmType": alarm_type_name,
                "meaning": meaning,
                "guidelines": guidelines
            })
    
    # 保存为JSON文件 (这部分逻辑保持不变)
    try:
        with open("alarmcontent.json", "w", encoding="utf-8") as f:
            json.dump(area_alarms, f, ensure_ascii=False, indent=4)
        print(f"成功为 '{target_area}' 保存 {len(area_alarms)} 条预警信息到 alarmcontent.json")
        if len(area_alarms) == 0:
            print(f"提示: 未找到 '{target_area}' 的当前预警信息，可能当前没有预警。")
    except Exception as e:
        print(f"保存文件失败: {e}")

if __name__ == "__main__":
    fetch_and_parse_alarm_data()
