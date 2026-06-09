import time
import re
import os  # Thêm thư viện os để kiểm tra file tồn tại
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# =========================
# 1. DANH SÁCH CÁC PHIM MỚI
# =========================
MOVIE_PAGES = {

    # "Film Name": "Link",
}

MAX_REVIEWS_PER_MOVIE = 100
OUTPUT_FILE = "film_reviews_dataset.csv"  # Giữ nguyên tên file cũ của bạn

# =========================
# 2. SETUP CHROME
# =========================
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# =========================
# 3. LOGIN THỦ CÔNG
# =========================
driver.get("https://www.imdb.com/")
print("Nếu cần đăng nhập IMDb thì đăng nhập thủ công trên Chrome vừa mở.")
input("Sau khi đăng nhập xong, quay lại Terminal và nhấn ENTER...")

# =========================
# 4. HÀM LẤY RATING
# =========================
def extract_rating(text):
    match = re.search(r"(\d{1,2})/10", text)
    if match:
        return int(match.group(1))
    return None

# =========================
# 5. HÀM CÀO REVIEW
# =========================
def scrape_reviews(movie_name, url):
    driver.get(url)
    time.sleep(5)

    reviews = []
    seen_reviews = set()

    while len(reviews) < MAX_REVIEWS_PER_MOVIE:
        time.sleep(2)

        elements = driver.find_elements(
            By.CSS_SELECTOR,
            '[data-testid="review-overflow"]'
        )

        for element in elements:
            review_text = driver.execute_script(
                "return arguments[0].innerText;",
                element
            ).strip()

            if not review_text or len(review_text) < 20:
                continue
            if review_text in seen_reviews:
                continue

            seen_reviews.add(review_text)

            full_card_text = driver.execute_script(
                """
                let el = arguments[0];
                let parent = el.closest('article, li, div');
                return parent ? parent.innerText : el.innerText;
                """,
                element
            )

            rating = extract_rating(full_card_text)

            reviews.append({
                "movie_name": movie_name,
                "review_id": len(reviews) + 1,
                "rating": rating,
                "review_text": review_text,
                "review_length": len(review_text),
                "source_url": url
            })

            if len(reviews) >= MAX_REVIEWS_PER_MOVIE:
                break

        if len(reviews) >= MAX_REVIEWS_PER_MOVIE:
            break

        # Cuộn xuống cuối trang
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Bấm nút Load More nếu có
        clicked = False
        buttons = driver.find_elements(By.TAG_NAME, "button")

        for btn in buttons:
            try:
                btn_text = btn.text.lower()
                if "load more" in btn_text or "more" in btn_text:
                    driver.execute_script("arguments[0].click();", btn)
                    clicked = True
                    time.sleep(3)
                    break
            except:
                pass

        if not clicked:
            print(f"{movie_name}: không còn nút Load More")
            break

    return reviews

# =========================
# 6. CHẠY SCRAPER VÀ LƯU NỐI TIẾP
# =========================
for movie_name, url in MOVIE_PAGES.items():
    print("=" * 50)
    print(f"Đang cào phim: {movie_name}")

    movie_reviews = scrape_reviews(movie_name, url)
    
    if movie_reviews:
        df_temp = pd.DataFrame(movie_reviews)
        
        # Kiểm tra xem file đã tồn tại chưa
        file_exists = os.path.isfile(OUTPUT_FILE)
        
        # Cốt lõi của việc tiếp tục lưu vào file: mode='a'
        df_temp.to_csv(
            OUTPUT_FILE,
            mode='a', 
            index=False,
            header=not file_exists,  # Chỉ in header nếu file chưa từng tồn tại
            encoding="utf-8-sig"
        )

        print(f"{movie_name}: lấy được {len(movie_reviews)} reviews")
        print(f"Đã LƯU NỐI TIẾP vào {OUTPUT_FILE}")
    else:
        print(f"{movie_name}: Không lấy được review nào.")

    time.sleep(5)

# =========================
# 7. TỔNG KẾT FILE CSV 
# =========================
print("=" * 50)
print(f"HOÀN TẤT SCRAPING CÁC PHIM MỚI")

# Đọc lại toàn bộ file để báo cáo tổng số dòng hiện tại
if os.path.isfile(OUTPUT_FILE):
    df_final = pd.read_csv(OUTPUT_FILE)
    print(f"Tổng số reviews có trong file hiện tại: {len(df_final)}")
    print(f"Đã lưu tại file: {OUTPUT_FILE}")

# =========================
# 8. ĐÓNG BROWSER
# =========================
driver.quit()
