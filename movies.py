import time
import re
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# =========================
# 1. DANH SÁCH 50 PHIM
# =========================
MOVIE_PAGES = {
    "Whiplash": "https://www.imdb.com/title/tt2582802/reviews/",
}

MAX_REVIEWS_PER_MOVIE = 100
OUTPUT_FILE = "film_reviews_dataset.csv"


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

        print(f"{movie_name}: tìm thấy {len(elements)} review elements")

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

            print(f"Collected {len(reviews)}/{MAX_REVIEWS_PER_MOVIE}")

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
# 6. CHẠY SCRAPER
# =========================
all_reviews = []

for movie_name, url in MOVIE_PAGES.items():
    print("=" * 50)
    print(f"Đang cào phim: {movie_name}")

    movie_reviews = scrape_reviews(movie_name, url)
    all_reviews.extend(movie_reviews)

    # Lưu tạm sau mỗi phim để tránh mất data
    df_temp = pd.DataFrame(all_reviews)
    df_temp.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"{movie_name}: lấy được {len(movie_reviews)} reviews")
    print(f"Đã lưu tạm vào {OUTPUT_FILE}")

    time.sleep(5)


# =========================
# 7. LƯU FILE CSV CUỐI
# =========================
df = pd.DataFrame(all_reviews)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("=" * 50)
print(f"HOÀN TẤT")
print(f"Tổng số reviews: {len(df)}")
print(f"Đã lưu file: {OUTPUT_FILE}")
print(df.head())


# =========================
# 8. ĐÓNG BROWSER
# =========================
driver.quit()