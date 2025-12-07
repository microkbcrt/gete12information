from DrissionPage import ChromiumPage, ChromiumOptions
import sys

def fetch_rebang_xiaohongshu():
    # --- GitHub Actions 专用配置开始 ---
    co = ChromiumOptions()
    # 1. 开启无头模式（必须，因为GitHub Actions没有显示器）
    co.set_headless(True)
    # 2. Linux 环境必须添加 --no-sandbox，否则无法启动 Chrome
    co.set_argument('--no-sandbox')
    # 3. 禁用 GPU，增加稳定性
    co.set_argument('--disable-gpu')
    
    # 尝试自动查找系统中的浏览器路径
    co.auto_port()

    # 初始化页面
    page = ChromiumPage(addr_or_opts=co)
    # --- GitHub Actions 专用配置结束 ---

    file_path = "xiaohongshurank.txt"

    try:
        print("正在访问 rebang.today ...")
        page.get('https://rebang.today/home?tab=xiaohongshu')
        
        # 等待数据加载 (最多等待 15 秒)
        # Cloudflare 验证可能会导致加载变慢
        print("正在等待数据渲染...")
        if not page.wait.ele_displayed('css:ul li a[title]', timeout=15):
            print("❌ 加载超时或被 Cloudflare 拦截。")
            # 可以在这里打印 page.html 查看是否是验证码页面
            sys.exit(0) # 退出但不报错，避免导致整个 Workflow 失败

        # 提取数据
        links = page.eles('css:ul li a[title]')
        
        if not links:
            print("❌ 未找到列表元素")
            return

        with open(file_path, "w", encoding="utf-8") as f:
            count = 0
            for link in links:
                title_text = link.attr('title')
                if title_text:
                    f.write(title_text + "\n")
                    count += 1
        
        print(f"✅ 成功获取 {count} 条小红书热搜，已保存至 {file_path}")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
        # 这里不抛出异常，防止阻断后续步骤，但打印错误日志
    
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_rebang_xiaohongshu()
