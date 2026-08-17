import json
from services.conflict_resolver_service import ConflictResolverService

print("⚙️ Initializing Conflict Resolver Service...")
resolver = ConflictResolverService()

def run_test():
    # حدیث ۱: وجوب نماز جمعه
    hadith_1 = "عَنْ زُرَارَةَ، عَنْ أَبِي جَعْفَرٍ (ع) قَالَ: صَلَاةُ الْجُمُعَةِ فَرِيضَةٌ وَ الِاجْتِمَاعُ إِلَيْهَا فَرِيضَةٌ مَعَ الْإِمَامِ فَإِنْ تَرَكَ رَجُلٌ مِنْ غَيْرِ عِلَّةٍ ثَلَاثَ جُمَعٍ فَقَدْ تَرَكَ ثَلَاثَ فَرَائِضَ."
    
    # حدیث ۲: عدم وجوب/اشتراط به امام معصوم
    hadith_2 = "عَنْ زُرَارَةَ، عَنْ أَبِي عَبْدِ اللَّهِ (ع) قَالَ: لَا تَكُونُ الْجُمُعَةُ إِلَّا مَعَ إِمَامٍ عَادِلٍ مَعْصُومٍ فَإِذَا لَمْ يَكُنْ إِمَامٌ فَلَا جُمُعَةَ وَ الصَّلَاةُ ظُهْرٌ أَرْبَعُ رَكَعَاتٍ."

    print("\n🚀 Running Conflict Resolution Test on Friday Prayer Hadiths...")
    verdict = resolver.resolve_conflict(hadith_1, hadith_2)

    print("\n" + "🌟"*40)
    print("        CONFLICT RESOLUTION VERDICT")
    print("🌟"*40)
    print(f"🔍 Conflict Detected? : {verdict['is_conflict_detected']}")
    print(f"⛓️ Sanad Comparison  : {verdict['sanad_comparison']}")
    print(f"📖 Quran Alignment   : {verdict['quran_tarjih']}")
    print(f"🎭 Taqiyyah Analysis : {verdict['taqiyyah_analysis']}")
    print(f"📐 Rule Applied      : {verdict['tarjih_rule_applied']}")
    print(f"📌 Final Verdict     : {verdict['final_verdict']}")
    print(f"\n📝 Detailed Reasoning:\n{verdict['detailed_reasoning']}")
    print("🌟"*40)

if __name__ == "__main__":
    run_test()