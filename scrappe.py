import requests
from bs4 import BeautifulSoup
import time
import os


def scrape_moajem(vol_num, start_page, end_page):
    print(f"🚀 Starting to scrape Mo'jam al-Rijal - Volume {vol_num}...")

    # ساخت مسیر ذخیره‌سازی تو پوشه دیتابیس رجال
    output_dir = os.path.join("data", "raw_epubs", "rijal")
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"moajem-{vol_num}.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        # حلقه روی صفحات کتاب
        for page in range(start_page, end_page + 1):
            # آدرس دقیق جلد و صفحه در سایت کتابخانه فقاهت
            url = f"https://lib.eshia.ir/14036/{vol_num}/{page}"

            try:
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')

                    # پیدا کردن سلول اصلی محتوا
                    content_td = soup.find('td', class_='book-page-show')

                    if content_td:
                        # 🚀 [ترفند جدید]: استخراج مستقیم تمام تگ‌های p
                        p_tags = content_td.find_all('p')

                        # اگر تگ p پیدا شد، متن‌هاشون رو استخراج می‌کنیم
                        if p_tags:
                            # separator=' ' باعث میشه بین کلمات به هم چسبیده (مثل داخل spanها) فاصله بیفته
                            clean_text = '\n\n'.join([p.get_text(separator=' ', strip=True) for p in p_tags])

                            # قالب‌بندی تمیز برای هوش مصنوعی
                            f.write(f"\n\n--- [جلد {vol_num} - صفحه {page}] ---\n\n")
                            f.write(clean_text)

                            print(f"✔️ Page {page} scraped and saved.")
                        else:
                            print(f"⚠️ Page {page}: Paragraphs (<p>) not found in content.")
                    else:
                        print(f"⚠️ Page {page}: Main content cell (td) not found.")
                else:
                    print(f"❌ Page {page}: Failed with status {res.status_code}")

            except Exception as e:
                print(f"❌ Page {page} Error: {e}")

            # برای جلوگیری از بلاک شدن توسط سایت، نیم ثانیه مکث می‌کنیم
            time.sleep(0.5)

    print(f"\n🎉 SUCCESS! Clean text saved to {file_path}")
    print("💡 Now you can run: python ingest.py --collection rijal")


if __name__ == "__main__":
    # نیازمندی‌ها: pip install requests beautifulsoup4
    # در حال حاضر جلد 2، از صفحه 1 تا 20 استخراج می‌شود (برای تست سریع)
    # scrape_moajem(vol_num=1, start_page=1, end_page=483)
    # scrape_moajem(vol_num=3, start_page=1, end_page=386)
    # scrape_moajem(vol_num=4, start_page=1, end_page=448)
    # scrape_moajem(vol_num=5, start_page=1, end_page=491)
    # scrape_moajem(vol_num=6, start_page=1, end_page=490)
    # scrape_moajem(vol_num=7, start_page=1, end_page=468)
    # scrape_moajem(vol_num=8, start_page=1, end_page=492)
    # scrape_moajem(vol_num=9, start_page=1, end_page=547)
    # scrape_moajem(vol_num=10, start_page=1, end_page=552)
    # scrape_moajem(vol_num=11, start_page=1, end_page=527)
    # scrape_moajem(vol_num=12, start_page=1, end_page=621)
    # scrape_moajem(vol_num=13, start_page=1, end_page=385)
    # scrape_moajem(vol_num=14, start_page=1, end_page=484)
    # scrape_moajem(vol_num=15, start_page=1, end_page=452)
    # scrape_moajem(vol_num=16, start_page=1, end_page=439)
    # scrape_moajem(vol_num=17, start_page=1, end_page=466)
    # scrape_moajem(vol_num=18, start_page=1, end_page=462)
    # scrape_moajem(vol_num=19, start_page=1, end_page=514)
    # scrape_moajem(vol_num=20, start_page=1, end_page=451)
    # scrape_moajem(vol_num=21, start_page=1, end_page=342)
    # scrape_moajem(vol_num=22, start_page=1, end_page=430)
    # scrape_moajem(vol_num=23, start_page=1, end_page=384)
    scrape_moajem(vol_num=24, start_page=1, end_page=353)


    # https://lib.eshia.ir/14028/1/150
    # https://lib.eshia.ir/10241/1/2
    # https://lib.eshia.ir/86760/1/489
    # https://lib.eshia.ir/14010/1/344