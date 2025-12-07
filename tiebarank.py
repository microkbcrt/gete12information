import requests
from bs4 import BeautifulSoup

def fetch_tieba_hot_topics():
    # 目标URL
    url = "https://tieba.baidu.com/hottopic/browse/topicList?res_type=1"

    # 设置请求头，伪装成浏览器，防止被百度拦截
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        # 1. 发送请求
        print(f"正在请求: {url} ...")
        response = requests.get(url, headers=headers)
        response.raise_for_status() # 如果请求失败则抛出异常
        response.encoding = 'utf-8' # 确保编码正确

        # 2. 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 3. 定位元素
        # 查找 ul class="topic-top-list" 下面的所有 class 为 "topic-text" 的 a 标签
        # CSS选择器语法: .class_name 代表 class
        titles = soup.select('ul.topic-top-list .topic-text')

        if not titles:
            print("未找到相关话题，可能是页面结构发生变化或反爬虫限制。")
            return

        # 4. 提取文字并保存到文件
        filename = "tiebarank.txt"
        with open(filename, "w", encoding="utf-8") as f:
            count = 0
            for item in titles:
                # 获取标签内的文本并去除首尾空格
                title_text = item.get_text().strip()
                if title_text:
                    f.write(title_text + "\n")
                    count += 1
        
        print(f"成功获取 {count} 条热议话题，已保存至 {filename}")

    except requests.exceptions.RequestException as e:
        print(f"网络请求出错: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    fetch_tieba_hot_topics()