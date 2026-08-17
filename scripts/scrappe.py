import re

import requests
from bs4 import BeautifulSoup
import time
import os


def scrape_moajem(vol_num, start_page, end_page):
    print(f"🚀 Starting to scrape al-Estebsar - Volume {vol_num}...")

    # ساخت مسیر ذخیره‌سازی تو پوشه دیتابیس رجال
    output_dir = os.path.join("data", "raw_epubs", "revayat-hadith")
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"estebsar-{vol_num}.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        # حلقه روی صفحات کتاب
        for page in range(start_page, end_page + 1):
            # آدرس دقیق جلد و صفحه در سایت کتابخانه فقاهت
            url = f"https://lib.eshia.ir/11002/{vol_num}/{page}"

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
    print("💡 Now you can run: python ingest.py --collection revayat-hadith")


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
    # scrape_moajem(vol_num=1, start_page=1, end_page=506)
    # scrape_moajem(vol_num=2, start_page=1, end_page=350)
    # scrape_moajem(vol_num=3, start_page=1, end_page=391)
    # scrape_moajem(vol_num=4, start_page=1, end_page=357)


    def scrape(col_name, title, link, vol_num, start_page, end_page):
        print(f"🚀 Starting to scrape {title} - Volume {vol_num}...")

        # ساخت مسیر ذخیره‌سازی تو پوشه دیتابیس رجال
        output_dir = os.path.join("data", "raw_epubs", col_name)
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, f"{title}-{vol_num}.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            # حلقه روی صفحات کتاب
            for page in range(start_page, end_page + 1):
                # آدرس دقیق جلد و صفحه در سایت کتابخانه فقاهت
                url = f"{link}/{vol_num}/{page}"

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
        print(f"💡 Now you can run: python ingest.py --collection {col_name}")

    def scrapeWithoutPTag(col_name, title, link, vol_num, start_page, end_page):
        print(f"🚀 Starting to scrape {title} - Volume {vol_num}...")

        # ساخت مسیر ذخیره‌سازی تو پوشه دیتابیس رجال
        output_dir = os.path.join("data", "raw_epubs", col_name)
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, f"{title}-{vol_num}.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            # حلقه روی صفحات کتاب
            for page in range(start_page, end_page + 1):
                # آدرس دقیق جلد و صفحه در سایت کتابخانه فقاهت
                url = f"{link}/{vol_num}/{page}"

                try:
                    res = requests.get(url, timeout=10)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, 'html.parser')

                        # پیدا کردن سلول اصلی محتوا
                        content_td = soup.find('td', class_='book-page-show')

                        if content_td:
                            # ۱. 💥 انفجار منوی مزاحم: پیدا کردن و حذف کامل sticky-menu
                            sticky_menu = content_td.find('div', class_='sticky-menue')
                            if sticky_menu:
                                sticky_menu.decompose()  # کلاً از HTML حذفش می‌کنه!

                            # ۲. تبدیل <br> ها به اینتر (برای حفظ شکستگیِ خطوط)
                            for br in content_td.find_all('br'):
                                br.replace_with('\n')

                            # ۳. [ترفند طلایی]: تزریق اینتر قبل از شماره راویان
                            # این کار باعث میشه شماره‌هایی مثل "175 -" حتماً برن خط جدید
                            # تا دیتابیس ChromaDB تو تفکیک راویان گیج نشه
                            for span in content_td.find_all('span', class_='KalamateKhas'):
                                span.insert_before('\n')

                            # ۴. استخراج متن تمیز
                            clean_text = content_td.get_text(separator=' ', strip=True)

                            # ۵. از بین بردن فاصله‌های خالی اضافه و اینترهای تکراری
                            clean_text = re.sub(r'\n\s+', '\n', clean_text)
                            clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)  # حداکثر دو اینتر پشت سر هم

                            if clean_text:
                                # قالب‌بندی تمیز برای هوش مصنوعی
                                f.write(f"\n\n--- [جلد {vol_num} - صفحه {page}] ---\n\n")
                                f.write(clean_text)
                                print(f"✔️ Page {page} scraped and saved.")
                            else:
                                print(f"⚠️ Page {page}: Content was empty after cleaning.")
                        else:
                            print(f"⚠️ Page {page}: Main content cell (td) not found.")
                    else:
                        print(f"❌ Page {page}: Failed with status {res.status_code}")

                except Exception as e:
                    print(f"❌ Page {page} Error: {e}")

                # برای جلوگیری از بلاک شدن توسط سایت، نیم ثانیه مکث می‌کنیم
                time.sleep(0.5)

        print(f"\n🎉 SUCCESS! Clean text saved to {file_path}")
        print(f"💡 Now you can run: python ingest.py --collection {col_name}")


    # scrape("revayat-hadith", "yahzar-al-faqih", "https://lib.eshia.ir/11021", 1, 1, 609)
    # scrape("revayat-hadith", "yahzar-al-faqih", "https://lib.eshia.ir/11021", 2, 1, 647)
    # scrape("revayat-hadith", "yahzar-al-faqih", "https://lib.eshia.ir/11021", 3, 1, 613)
    # scrape("revayat-hadith", "yahzar-al-faqih", "https://lib.eshia.ir/11021", 4, 1, 590)
    #
    # scrape("revayat-hadith", "tahziba-al-ahkam", "https://lib.eshia.ir/10083", 1, 1, 472)
    # scrape("revayat-hadith", "tahziba-al-ahkam", "https://lib.eshia.ir/10083", 2, 1, 385)
    # scrape("revayat-hadith", "tahziba-al-ahkam", "https://lib.eshia.ir/10083", 3, 1, 338)
    # scrape("revayat-hadith", "tahziba-al-ahkam", "https://lib.eshia.ir/10083", 4, 1, 339)
    # scrape("revayat-hadith", "tahziba-al-ahkam", "https://lib.eshia.ir/10083", 5, 1, 496)
    # scrape("revayat-hadith", "tahziba-al-ahkam", "https://lib.eshia.ir/10083", 6, 1, 406)
    # scrape("revayat-hadith", "tahziba-al-ahkam", "https://lib.eshia.ir/10083", 7, 1, 495)
    # scrape("revayat-hadith", "tahziba-al-ahkam", "https://lib.eshia.ir/10083", 8, 1, 327)
    # scrape("revayat-hadith", "tahziba-al-ahkam", "https://lib.eshia.ir/10083", 9, 1, 402)
    # scrape("revayat-hadith", "tahziba-al-ahkam", "https://lib.eshia.ir/10083", 10, 1, 320)
    #
    # scrape("revayat-hadith", "al-kafi", "https://lib.eshia.ir/11005", 1, 1, 567)
    # scrape("revayat-hadith", "al-kafi", "https://lib.eshia.ir/11005", 2, 1, 692)
    # scrape("revayat-hadith", "al-kafi", "https://lib.eshia.ir/11005", 3, 1, 585)
    # scrape("revayat-hadith", "al-kafi", "https://lib.eshia.ir/11005", 4, 1, 608)
    # scrape("revayat-hadith", "al-kafi", "https://lib.eshia.ir/11005", 5, 1, 594)
    # scrape("revayat-hadith", "al-kafi", "https://lib.eshia.ir/11005", 6, 1, 576)
    # scrape("revayat-hadith", "al-kafi", "https://lib.eshia.ir/11005", 7, 1, 479)
    # scrape("revayat-hadith", "al-kafi", "https://lib.eshia.ir/11005", 8, 1, 442)


    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 1, 1, 504)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 2, 1, 565)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 3, 1, 549)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 4, 1, 479)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 5, 1, 529)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 6, 1, 521)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 7, 1, 529)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 8, 1, 557)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 9, 1, 568)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 10, 1, 567)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 11, 1, 555)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 12, 1, 579)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 13, 1, 577)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 14, 1, 615)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 15, 1, 391)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 16, 1, 397)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 17, 1, 480)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 18, 1, 468)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 19, 1, 450)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 20, 1, 581)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 21, 1, 579)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 22, 1, 451)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 23, 1, 412)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 24, 1, 446)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 25, 1, 482)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 26, 1, 328)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 27, 1, 423)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 28, 1, 396)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 29, 1, 416)
    # scrape("revayat-hadith", "vasael-o-shia", "https://lib.eshia.ir/11025", 30, 1, 553)

    # moral & lifestyle

    # scrapeWithoutPTag("revayat-hadith", "tohaf-ol-oghol", "https://lib.eshia.ir/15139", 1, 1, 516)

    # scrape("revayat-hadith", "al-khesal", "https://lib.eshia.ir/15339", 1, 1, 340)
    # scrape("revayat-hadith", "al-khesal", "https://lib.eshia.ir/15339", 2, 1, 751)


    # scrape("revayat-hadith", "makarem-ol-akhlagh", "https://lib.eshia.ir/12840", 1, 1, 521)
    # scrape("revayat-hadith", "makarem-ol-akhlagh", "https://lib.eshia.ir/12840", 2, 1, 506)

    # Stories

    # scrape("revayat-hadith", "al-ershad", "https://lib.eshia.ir/27035", 1, 1, 364)
    # scrape("revayat-hadith", "al-ershad", "https://lib.eshia.ir/27035", 2, 1, 564)

    # scrape("revayat-hadith", "kamal-al-din", "https://lib.eshia.ir/27045", 1, 1, 564)
    # scrape("revayat-hadith", "kamal-al-din", "https://lib.eshia.ir/27045", 2, 1, 687)

    # scrape("revayat-hadith", "tafsir-al-qomi", "https://lib.eshia.ir/12015", 1, 1, 396)
    # scrape("revayat-hadith", "tafsir-al-qomi", "https://lib.eshia.ir/12015", 2, 1, 457)
    # scrape("revayat-hadith", "tarikh-al-yaghobi", "https://lib.eshia.ir/10382", 1, 1, 272)
    # scrape("revayat-hadith", "tarikh-al-yaghobi", "https://lib.eshia.ir/10382", 2, 1, 512)

    # scrape("revayat-hadith", "tarikh-al-amali", "https://lib.eshia.ir/15035", 1, 1, 419)

    # scrape("revayat-hadith", "waqat-siffin", "https://lib.eshia.ir/22035", 1, 1, 692)

    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 1, 1, 232)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 2, 1, 326)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 3, 1, 342)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 4, 1, 328)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 5, 1, 344)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 6, 1, 342)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 7, 1, 346)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 8, 1, 381)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 9, 1, 350)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 10, 1, 462)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 11, 1, 401)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 12, 1, 394)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 13, 1, 466)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 14, 1, 529)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 15, 1, 420)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 16, 1, 426)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 17, 1, 428)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 18, 1, 428)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 19, 1, 372)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 20, 1, 404)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 21, 1, 418)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 22, 1, 560)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 23, 1, 400)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 24, 1, 410)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 25, 1, 392)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 26, 1, 368)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 27, 1, 358)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 28, 1, 414)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 29, 1, 657)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 30, 1, 709)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 31, 1, 664)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 32, 1, 620)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 33, 1, 641)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 34, 1, 454)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 35, 1, 448)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 36, 1, 426)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 37, 1, 358)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 38, 1, 368)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 39, 1, 364)
    # scrape("bihar-al-anvar", "bihar-al-anvar", "https://lib.eshia.ir/11008", 40, 1, 364)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 41, 1, 372)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 42, 1, 346)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 43, 1, 376)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 44, 1, 400)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 45, 1, 414)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 46, 1, 376)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 47, 1, 420)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 48, 1, 336)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 49, 1, 348)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 50, 1, 348)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 51, 1, 390)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 52, 1, 396)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 53, 1, 346)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 54, 1, 408)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 55, 1, 263)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 56, 1, 431)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 57, 1, 386)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 58, 1, 392)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 59, 1, 406)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 60, 1, 398)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 61, 1, 338)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 62, 1, 366)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 63, 1, 352)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 64, 1, 338)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 65, 1, 336)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 66, 1, 564)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 67, 1, 392)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 68, 1, 402)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 69, 1, 420)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 70, 1, 412)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 71, 1, 438)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 72, 1, 350)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 73, 1, 416)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 74, 1, 430)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 75, 1, 478)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 76, 1, 384)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 77, 1, 448)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 78, 1, 464)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 79, 1, 331)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 80, 1, 386)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 81, 1, 406)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 82, 1, 382)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 83, 1, 396)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 84, 1, 389)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 85, 1, 346)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 86, 1, 376)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 87, 1, 364)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 88, 1, 340)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 89, 1, 392)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 90, 1, 388)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 91, 1, 396)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 92, 1, 397)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 93, 1, 402)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 94, 1, 412)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 95, 1, 486)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 96, 1, 397)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 97, 1, 394)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 98, 1, 432)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 99, 1, 396)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 100, 1, 464)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 101, 1, 384)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 102, 1, 326)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 103, 1, 400)
    scrape('bihar-al-anvar', 'bihar-al-anvar', 'https://lib.eshia.ir/11008', 104, 1, 442)

    # Imam Hossein

    # scrapeWithoutPTag("revayat-hadith", "maghtal-ol-hossein", "https://lib.eshia.ir/16064", 1, 1, 396)

    # Debate

    # scrapeWithoutPTag("revayat-hadith", "al-ehtejaj", "https://lib.eshia.ir/15016", 1, 1, 421)
    # scrapeWithoutPTag("revayat-hadith", "al-ehtejaj", "https://lib.eshia.ir/15016", 2, 1, 341)



