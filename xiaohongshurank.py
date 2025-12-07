from DrissionPage import ChromiumPage

def fetch_rebang_xiaohongshu():
    # 1. 初始化页面对象
    page = ChromiumPage()
    
    try:
        print("正在打开浏览器访问 rebang.today ...")
        # 访问目标网页
        page.get('https://rebang.today/home?tab=xiaohongshu')
        
        # 2. 等待数据加载 (修正点在这里)
        # 使用 .wait.ele_displayed() 等待元素显示
        print("正在等待数据加载...")
        if not page.wait.ele_displayed('css:ul li a[title]', timeout=10):
            print("加载超时，页面未显示相关数据。")
            return

        # 3. 提取数据
        # 查找所有符合规则的元素：在 ul li 下面的带有 title 属性的 a 标签
        links = page.eles('css:ul li a[title]')
        
        filename = "xiaohongshurank.txt"
        count = 0
        
        with open(filename, "w", encoding="utf-8") as f:
            for link in links:
                # 提取 title 属性
                title_text = link.attr('title')
                if title_text:
                    f.write(title_text + "\n")
                    count += 1
        
        print(f"抓取完成！成功获取 {count} 条热搜，已保存至 {filename}")

    except Exception as e:
        print(f"发生错误: {e}")
    
    finally:
        # 关闭浏览器（推荐关闭，否则后台会有很多浏览器进程）
        page.quit()

if __name__ == "__main__":
    fetch_rebang_xiaohongshu()
