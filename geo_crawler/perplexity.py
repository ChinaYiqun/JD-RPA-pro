from playwright.sync_api import sync_playwright
import time
import pandas as pd  
import os            

# —————— 新增：读取 queries.csv ——————
queries_file = "queries.csv"
if not os.path.exists(queries_file):
    print(f"❌ 未找到 {queries_file}，请确保文件存在")
    exit(1)

df = pd.read_csv(queries_file)
queries = df["query"].tolist()
intents = df.get("intent", [""] * len(queries)).tolist()  # 兼容无 intent 列

results = []  # 用于汇总结果

for idx, query in enumerate(queries):
    intent = intents[idx]
    print(f"\n[{idx+1}/{len(queries)}] 📥 正在处理：{query}")

    # —————— 启动新浏览器（每条独立）——————
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=f"./user_data",  # 每次用独立目录防冲突
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",           # 切换成本地的 Chrome 路径
            headless=False,
            bypass_csp=True,
            slow_mo=10,
            args=['--disable-blink-features=AutomationControlled', '--remote-debugging-port=9222']
        )
        page = browser.new_page()

        # 1. 打开 Perplexity
        page.goto("https://www.perplexity.ai")
        print("✅ 已打开 Perplexity")

        # 可选：首次运行时手动登录（后续因持久化可跳过）
        # 若已登录，下面这行可保留；若未登录，取消注释等待按钮
        # page.wait_for_selector("#ask-input", timeout=60000)

        # 2. 输入消息
        input_box = page.locator("#ask-input")
        input_box.fill(query)  # ← 改为当前 query
        print("✏️ 已输入消息")

        # 3. 发送
        time.sleep(1)
        page.keyboard.press("Enter")

        # 4. 等待回复生成（拷贝按钮出现）
        copy_button = page.wait_for_selector(
            "button[aria-label=\"拷贝\"]",
            timeout=90000  # 容忍长响应
        )
        print("✅ 回复已生成，找到复制按钮")


        # 5. 点击复制按钮
        copy_button.click()
        # 提取剪贴板内容
        answer_text = page.evaluate("navigator.clipboard.readText()")
        print(f"📝 提取到答案：{answer_text[:200]}...")  # 仅显示前200字符
        print("📋 已点击复制")

        # 6. 切换到 Sources 标签页
        try:
            link_tab = page.get_by_test_id("answer-mode-tabs-tab-sources").nth(0)
            link_tab.click()
            time.sleep(2)  # 等待加载
        except Exception as e:
            print(f"⚠️ 切换 Sources 失败：{e}")

        # 7. 提取前三条链接
        try:
            urls = page.locator("a.group\\/source").evaluate_all(
                "els => els.slice(0, 3).map(el => (el.href || '').trim())"
            )
        except Exception as e:
            print(f"⚠️ 提取链接失败：{e}")
            urls = []

        print("前三条链接：")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")

        # —————— 保存本条结果 ——————
        results.append({
            "intent": intent,
            "query": query,
            "answer": answer_text[:2000],  # Excel 限制长度
            "url1": urls[0] if len(urls) > 0 else "",
            "url2": urls[1] if len(urls) > 1 else "",
            "url3": urls[2] if len(urls) > 2 else "",
        })

        # 临时保存（防中断丢失）
        pd.DataFrame(results).to_excel("perplexity_batch_results.xlsx", index=False)
        print("💾 本条结果已追加保存")

        # 8. 关闭浏览器（关键！）
        browser.close()
        print("CloseOperation: 浏览器已关闭 ✅")

        # 每条间隔，降低风控
        time.sleep(2)

# —————— 最终汇总输出 ——————
print("\n🎉 全部完成！共处理", len(results), "条")
pd.DataFrame(results).to_excel("perplexity_batch_results.xlsx", index=False)
print("📥 最终结果已写入 perplexity_batch_results.xlsx")