from DrissionPage import ChromiumPage, ChromiumOptions
import sys

def fetch_rebang_xiaohongshu():
    # --- GitHub Actions 专用配置开始 ---
    co = ChromiumOptions()
    
    # 🟢 修正点 1: v4.x 版本使用 .headless(True) 开启无头模式
    co.headless(True)
    
    # 2. Linux 环境必须添加 --no-sandbox
    co.set_argument('--no-sandbox')
    # 3. 禁用 GPU (Linux环境推荐)
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
        print("正在等待数据渲染...")
        # v4.x 使用 ele_displayed 等待元素显示
        if not page.wait.ele_displayed('css:ul li a[title]', timeout=15):
            print("❌ 加载超时或被 Cloudflare 拦截。")
            sys.exit(0) 

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
        # 允许脚本报错退出，以便在 Action 日志中看到红叉（可选）
        sys.exit(1)
    
    finally:
        # 关闭浏览器
        try:
            page.quit()
        except:
            pass

if __name__ == "__main__":
    fetch_rebang_xiaohongshu()
