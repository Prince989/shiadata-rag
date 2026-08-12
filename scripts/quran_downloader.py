import requests
import json
import os

def fetch_quran_data():
    print("==================================================")
    print("🕋 SHIA-DATA: TRI-LINGUAL QURAN DOWNLOADER 🕋")
    print("==================================================")
    
    arabic_url = "http://api.alquran.cloud/v1/quran/quran-uthmani"
    persian_url = "http://api.alquran.cloud/v1/quran/fa.makarem"
    english_url = "http://api.alquran.cloud/v1/quran/en.sahih"  # 👈 اضافه شدن انگلیسی
    
    print("📥 1. Downloading Arabic Text...")
    ar_response = requests.get(arabic_url).json()
    
    print("📥 2. Downloading Persian Translation (Makarem)...")
    fa_response = requests.get(persian_url).json()
    
    print("📥 3. Downloading English Translation (Sahih)...")
    en_response = requests.get(english_url).json()

    arabic_surahs = ar_response["data"]["surahs"]
    persian_surahs = fa_response["data"]["surahs"]
    english_surahs = en_response["data"]["surahs"]
    
    quran_db = []
    
    print("⚙️ 4. Merging into a Tri-lingual JSON...")
    for s_idx in range(len(arabic_surahs)):
        surah_ar = arabic_surahs[s_idx]
        surah_fa = persian_surahs[s_idx]
        surah_en = english_surahs[s_idx]
        
        surah_name_en = surah_ar["englishName"]
        surah_name_ar = surah_ar["name"]
        
        for a_idx in range(len(surah_ar["ayahs"])):
            ayah_ar = surah_ar["ayahs"][a_idx]
            ayah_fa = surah_fa["ayahs"][a_idx]
            ayah_en = surah_en["ayahs"][a_idx]
            
            ayah_data = {
                "surah_number": surah_ar["number"],
                "surah_name_ar": surah_name_ar,
                "surah_name_en": surah_name_en,
                "ayah_number": ayah_ar["numberInSurah"],
                "arabic_text": ayah_ar["text"],
                "persian_translation": ayah_fa["text"],
                "english_translation": ayah_en["text"],
                # فیلد طلایی جستجوی سه‌زبانه:
                "searchable_text": f"Surah {surah_name_en} - سورة {surah_name_ar} | Ayah {ayah_ar['numberInSurah']}\n[AR]: {ayah_ar['text']}\n[FA]: {ayah_fa['text']}\n[EN]: {ayah_en['text']}"
            }
            quran_db.append(ayah_data)

    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "quran.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(quran_db, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Success! Saved {len(quran_db)} Ayahs with translations to {output_path}")

if __name__ == "__main__":
    fetch_quran_data()