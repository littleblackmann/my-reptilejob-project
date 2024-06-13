from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# 設置 Chrome 瀏覽器的選項
chrome_options = Options()
chrome_options.add_argument("--incognito")  # 開啟無痕模式
chrome_options.add_argument("--headless")  # 開啟無頭模式，若要看見瀏覽器操作過程，可移除此選項

# 設置 ChromeDriver 的路徑
chrome_driver_path = '/opt/homebrew/bin/chromedriver'  # 替換為你的 chromedriver 路徑
service = Service(chrome_driver_path)

# 創建 WebDriver 對象
driver = webdriver.Chrome(service=service, options=chrome_options)

# 定義目標 URL 和參數
base_url = "https://www.104.com.tw/jobs/search/?"
params = {
    'ro': '0',  # 工作類型。'0' 代表全職工作。其他可能的值包括：
                # '1': 兼職工作
                # '2': 企業實習
                # '3': 學生實習

    'kwop': '7',  # 關鍵字範圍。'7' 表示搜索範圍包括標題和內文。其他可能的值包括：
                  # '1': 只搜索標題
                  # '2': 只搜索內文
                  # '4': 搜索公司名稱
                  # '6': 搜索公司簡介

    'keyword': '',  # 關鍵字。這裡設置為空字串，會在程序中動態更新為不同的職位名稱（例如 '後端工程師' 等）。

    'area': '6001001000',  # 搜索的地區代碼。'6001001000' 代表台北市。可以使用不同的地區代碼來代表其他地理位置。
                           # 例如：
                           # '6001002000': 新北市
                           # '6001003000': 桃園市
                           # 更多地區代碼可參考104網站地區選單。

    'isnew': '30',  # 職缺的更新日期範圍。'30' 表示只顯示最近一個月的新職缺。其他可能的值包括：
                    # '1': 最近一天
                    # '7': 最近一周
                    # '14': 最近兩周

    'page': '1'  # 搜索結果的頁碼。這裡初始設置為 '1'，在爬取過程中會動態更新，用於控制結果的分頁顯示。
}

keywords = ['後端工程師', '軟體工程師', '雲端工程師', '全端工程師', '數據分析師', 'pytnon工程師', 'Backend',]
job_content_list = []
search_terms = ['無經驗', '培訓', '養成班']

print("開始爬取工作內容...")

for keyword in keywords:
    params['keyword'] = keyword
    print(f"正在搜尋關鍵字: {keyword}")
    no_results_count = 0  # 用來計算連續沒有結果的頁數

    for page in range(1, 100):  # 爬取最多100頁
        params['page'] = str(page)
        print(f"正在爬取第 {page} 頁...")
        url = base_url + '&'.join([f'{key}={value}' for key, value in params.items()])
        driver.get(url)
        print("頁面加載完成")
        time.sleep(2)  # 等待頁面加載

        try:
            job_cards = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.b-block--top-bord'))
            )
            print(f"找到 {len(job_cards)} 條職位信息.")

            if len(job_cards) == 0:
                no_results_count += 1
                if no_results_count >= 2:  # 如果連續2頁都沒有結果，假設已達到末尾
                    print(f"連續 {no_results_count} 頁無結果，跳過到下一個關鍵字。")
                    break
            else:
                no_results_count = 0  # 重置連續無結果頁數計數

            for card in job_cards:
                job_description = card.text
                job_link = card.find_element(By.CSS_SELECTOR, 'a.js-job-link').get_attribute('href')  # 獲取職位詳情頁面的URL
                if any(term in job_description for term in search_terms):
                    job_content_list.append({
                        'keyword': keyword,
                        'description': job_description,
                        'url': job_link  # 將URL加入到儲存的數據中
                    })
        except Exception as e:
            print(f"第 {page} 頁遇到錯誤：{e}")
            no_results_count += 1
            if no_results_count >= 2:  # 如果連續2頁都出現錯誤，跳過到下一個關鍵字
                print(f"連續 {no_results_count} 頁遇到錯誤，跳過到下一個關鍵字。")
                break

print("爬取完成，正在保存結果...")

# 保存為 CSV 檔案
df = pd.DataFrame(job_content_list)
df.to_csv('filtered_job_contents_with_links.csv', index=False, encoding='utf-8-sig')

print(f"保存成功，共保存 {len(job_content_list)} 條符合條件的工作內容到 'filtered_job_contents_with_links.csv' 檔案中.")

# 關閉瀏覽器
driver.quit()
