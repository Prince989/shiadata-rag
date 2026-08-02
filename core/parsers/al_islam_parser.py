from bs4 import BeautifulSoup
from typing import List, Dict
import zipfile
import re
from core.models import ParsedChunk


class AlIslamEpubParser:
    """
    پارسری مخصوص استخراج متن و منابع از فایل‌های EPUB دانلود شده از سایت Al-Islam.org.
    این کلاس توانایی خواندن مستقیم فایل فشرده EPUB و استخراج HTMLهای آن را دارد.
    """

    def __init__(self, epub_path: str):
        self.epub_path = epub_path
        self.book_title = self._extract_book_title_from_path(epub_path)

    def _extract_book_title_from_path(self, path: str) -> str:
        # استخراج نام کتاب از اسم فایل (به عنوان یک فالبک)
        # مثلاً از 'data/raw_epubs/al-ghayba.epub' خروجی میده 'al-ghayba'
        filename = path.split('/')[-1].split('\\')[-1]
        return filename.replace('.epub', '').replace('-', ' ').title()

    def parse(self) -> List[ParsedChunk]:
        """
        اجرای اصلی پارسر: فایل EPUB را می‌خواند و لیستی از چانک‌های غنی‌شده برمی‌گرداند.
        """
        all_chunks = []

        # 1. باز کردن فایل EPUB به عنوان یک فایل Zip
        try:
            with zipfile.ZipFile(self.epub_path, 'r') as epub:
                # استخراج تمام فایل‌های HTML/XHTML داخل EPUB
                html_files = [f for f in epub.namelist() if f.endswith(('.html', '.xhtml', '.htm'))]

                print(f"📖 Found {len(html_files)} HTML files in EPUB.")

                # 2. پردازش تک‌تک فایل‌های HTML
                for html_file in html_files:
                    with epub.open(html_file) as file:
                        html_content = file.read().decode('utf-8')
                        chunks_from_file = self._parse_single_html(html_content)
                        all_chunks.extend(chunks_from_file)

        except Exception as e:
            print(f"❌ Error reading EPUB file {self.epub_path}: {str(e)}")

        return all_chunks

    def _parse_single_html(self, html_content: str) -> List[ParsedChunk]:
        soup = BeautifulSoup(html_content, 'html.parser')
        chunks = []

        # استخراج دیکشنری پاورقی‌ها
        footnotes_dict = self._extract_footnotes(soup)

        current_chapter = "General Context"

        # مخزن‌های موقت برای جمع‌آوری اطلاعاتِ یک بخش (Section-Based)
        section_text_buffer = []
        section_refs_buffer = []

        # تابع داخلی برای پکیج کردن و ذخیره‌ی مخزن
        def save_buffer_as_chunk():
            if section_text_buffer:
                # 1. چسباندن پاراگراف‌های یک بخش به هم (ایده B)
                combined_text = "\n\n".join(section_text_buffer)

                # 2. تزریقِ تیتر به ابتدای متنِ یکپارچه (ایده A)
                text_for_embedding = f"[Topic: {current_chapter}]\n{combined_text}"

                # 3. پاکسازی پاورقی‌های تکراری و تزریق به انتهای متن
                unique_refs = list(dict.fromkeys(section_refs_buffer))
                if unique_refs:
                    footnotes_str = " | ".join(unique_refs)
                    text_for_embedding = f"{text_for_embedding}\n\n[Footnotes: {footnotes_str}]"

                # ساخت متادیتا
                metadata = {
                    "book_title": self.book_title,
                    "chapter": current_chapter,
                    "footnotes": unique_refs if unique_refs else ["None"]
                }

                chunks.append(ParsedChunk(text=text_for_embedding, metadata=metadata))

                # خالی کردن مخزن برای بخش (تیتر) بعدی
                section_text_buffer.clear()
                section_refs_buffer.clear()

        # حرکت روی المان‌های HTML
        for element in soup.find_all(['h1', 'h2', 'h3', 'p']):

            # وقتی به یک تیتر جدید می‌رسیم
            if element.name in ['h1', 'h2', 'h3']:
                save_buffer_as_chunk()  # مخزن قبلی رو کامل سیو کن
                current_chapter = element.get_text(strip=True)  # تیتر جدید رو بردار
                continue

            # وقتی به پاراگراف می‌رسیم
            if element.name == 'p':
                refs = []
                # استخراج پاورقی‌های همین پاراگراف
                for a_tag in element.find_all('a', class_='see-footnote'):
                    href = a_tag.get('href', '')
                    if '#' in href:
                        fn_id = href.split('#')[1]
                        if fn_id in footnotes_dict:
                            refs.append(footnotes_dict[fn_id])
                    a_tag.decompose()  # پاک کردن عدد ارجاع از متن

                clean_text = element.get_text(strip=True)
                if clean_text:
                    # پاراگراف و پاورقی‌هاش رو بریز تو مخزنِ این بخش
                    section_text_buffer.append(clean_text)
                    section_refs_buffer.extend(refs)

        # انتهای فایل: آخرین مخزن رو هم سیو کن
        save_buffer_as_chunk()

        return chunks
    def _extract_footnotes(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        تمام پاورقی‌های انتهای یک HTML را استخراج می‌کند.
        """
        footnotes = {}
        # در سایت Al-Islam معمولاً پاورقی‌ها در تگ‌های <li class="footnote"> هستند
        for li in soup.find_all('li', class_='footnote'):
            fn_id = li.get('id')
            if not fn_id:
                continue

            # پاک کردن عدد ارجاع در خود پاورقی (مثلا "1. ")
            label_tag = li.find('a', class_='footnote-label')
            if label_tag:
                label_tag.decompose()

            fn_text = li.get_text(strip=True)
            footnotes[fn_id] = fn_text

        return footnotes