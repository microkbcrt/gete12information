from DrissionPage import ChromiumPage, ChromiumOptions
import sys

def fetch_rebang_xiaohongshu():
    # --- 关键修改开始 ---
    # 配置浏览器启动选项
    co = ChromiumOptions()
    # 1. 开启无头模式（不显示界面）
    co.set_headless()
    # 2. Linux/Docker 环境必须添加 --no-sandbox
    co.set_argument('--no-sandbox')
    # 3. 禁用 GPU 加速（防止某些 Linux 环境报错）
    co.set_argument('--disable-gpu')
    
    # 使用配置启动浏览器
    page = ChromiumPage(addr_or_opts=co)
    # --- 关键修改结束 ---
    
    try:
        print("正在访问 rebang.today ...")
        page.get('https://rebang.today/home?tab=xiaohongshu')
        
        # 等待数据加载
        print("正在等待数据渲染...")
        if not page.wait.ele_displayed('css:ul li a[title]', timeout=15):
            print("加载超时，页面可能触发了反爬虫验证 (Cloudflare)。")
            # 可以在这里打印页面源码调试
            # print(page.html)
            return

        links = page.eles('css:ul li a[title]')
        
        filename = "xiaohongshurank.txt"
        count = 0
        
        with open(filename, "w", encoding="utf-8") as f:
            for link in links:
                title_text = link.attr('title')
                if title_text:
                    f.write(title_text + "\n")
                    count += 1
        
        print(f"成功获取 {count} 条热搜")

    except Exception as e:
        print(f"发生错误: {e}")
        # 如果出错，非零退出，让 GitHub Actions 显示红叉
        sys.exit(1)
    
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_rebang_xiaohongshu()
