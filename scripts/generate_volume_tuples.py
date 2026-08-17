import sys

import requests
from bs4 import BeautifulSoup
import time


def generate_volume_tuples(collection_name, book_name, base_url, total_volumes):
    results = []

    # استفاده از Session برای بهینه‌سازی و حفظ اتصال (Keep-Alive)
    session = requests.Session()

    print(f"🚀 در حال استخراج اطلاعات برای {total_volumes} جلد از سایت...")

    for vol in range(1, total_volumes + 1):
        url = f"{base_url}/{vol}/1"

        try:
            # ارسال درخواست به صفحه اول هر جلد
            response = session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # جستجو برای تگ a با title='نمایش صفحه‌آخر'
            last_page_link = soup.find('a', title='نمایش صفحه‌آخر')

            if last_page_link and 'href' in last_page_link.attrs:
                href = last_page_link['href']
                # آدرس به شکل /11008/1/232 است. با اسپلیت کردن، عدد آخر را می‌گیریم
                last_page = int(href.strip('/').split('/')[-1])
            else:
                # در صورتی که کتاب فقط یک صفحه داشته باشد یا دکمه صفحه آخر نباشد
                print(f"⚠️ دکمه صفحه آخر برای جلد {vol} یافت نشد (احتمالاً تک صفحه‌ای است).")
                last_page = 1

            # ساختن تاپل (Tuple) دقیقاً با فرمتی که خواستی
            vol_tuple = (collection_name, book_name, base_url, vol, 1, last_page)
            results.append(vol_tuple)

            # نمایش پیشرفت کار
            print(f"✅ جلد {vol:03d} پردازش شد -> صفحه آخر: {last_page}")

            # یک وقفه نیم ثانیه‌ای برای جلوگیری از بن شدن آی‌پی
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"❌ خطا در ارتباط با جلد {vol}: {e}")
        except Exception as e:
            print(f"❌ خطای پردازش در جلد {vol}: {e}")

    return results


# ==========================================
# بخش اجرای اسکریپت
# ==========================================
if __name__ == "__main__":
    # تنظیمات ورودی
    COLLECTION_NAME = "bihar-al-anvar"
    BOOK_NAME = "bihar-al-anvar"
    BASE_URL = "https://lib.eshia.ir/11008"
    TOTAL_VOLUMES = 104

    # فراخوانی تابع
    final_data = generate_volume_tuples(COLLECTION_NAME, BOOK_NAME, BASE_URL, TOTAL_VOLUMES)

    # print("\n" + f"({COLLECTION_NAME},{BOOK_NAME},)")
    print("\n" + "=" * 50)
    print("🎉 خروجی نهایی:")
    print("=" * 50 + "\n")

    # چاپ تاپل‌ها در خطوط مجزا تا به راحتی کپی کنی
    for data in final_data:
        print(data)