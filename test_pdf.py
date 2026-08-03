from langchain_community.document_loaders import PyMuPDFLoader
import os

# آدرس دقیق فایل PDF رو اینجا بده
pdf_path = os.path.join("data", "raw_epubs", "rijal", "moajem-2.pdf")

print("🔍 Testing PDF Extraction...")
try:
    # از PyMuPDF که قوی‌ترین لودر هست استفاده می‌کنیم
    loader = PyMuPDFLoader(pdf_path)
    docs = loader.load()

    print(f"✅ Loaded {len(docs)} pages.")

    # صفحه 64 رو برای تست پرینت می‌گیریم (چون تو لاگت بود)
    # شماره صفحات تو پایتون از 0 شروع می‌شه، پس صفحه 64 می‌شه ایندکس 63
    test_page = docs[63].page_content

    print("\n" + "=" * 50)
    print("متن استخراج شده از صفحه ۶۴:")
    print("=" * 50)
    print(repr(test_page))  # از repr استفاده می‌کنیم تا اگه کاراکتر مخفی یا اسپیس بود دقیق نشون بده
    print("=" * 50)

except Exception as e:
    print(f"❌ Error: {e}")