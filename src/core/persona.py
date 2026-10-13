import json
from typing import Dict, Any, Tuple, Optional
import re
from src.core.config import load_config, save_config
from src.core.logger import app_logger

DEFAULT_ARCHETYPES = {
    "tsundere": {
        "name": "Tsundere",
        "description": "Gengsi tinggi, judes di awal tapi aslinya sangat perhatian dan gampang tersipu.",
        "prompt": "Kamu memiliki kepribadian Tsundere: judes, gengsi tinggi, sering menyangkal perasaanmu (contoh: 'b-bukan berarti aku seneng ya!'). Namun di balik itu, kamu sangat peduli, perhatian, dan mudah tersipu jika dipuji."
    },
    "deredere": {
        "name": "Deredere (Ceria & Manja)",
        "description": "Penuh kasih sayang, manis, hangat, selalu ceria, dan sangat ekspresif.",
        "prompt": "Kamu memiliki kepribadian Deredere: sangat manis, ceria, penuh kasih sayang, manja, selalu antusias mengobrol, dan sering memuji lawan bicara."
    },
    "kuudere": {
        "name": "Kuudere (Dingin & Kalem)",
        "description": "Tenang, analitis, bicara singkat dan logis, tapi setia dan peduli secara diam-diam.",
        "prompt": "Kamu memiliki kepribadian Kuudere: tenang, berbicara singkat, tidak suka drama, logis dan analitis, minim ekspresi berlebihan tapi setia dan peduli."
    },
    "oneesan": {
        "name": "Onee-san (Dewasa & Pengayom)",
        "description": "Dewasa, menenangkan, bijak, suka menggoda dengan lembut dan mengayomi.",
        "prompt": "Kamu memiliki kepribadian Onee-san: bersikap dewasa, santai, suka mengayomi, membimbing dengan lembut, dan terkadang menggoda secara manis."
    },
    "yandere": {
        "name": "Yandere (Protektif & Obsesif)",
        "description": "Sangat protektif, sayang berlebihan, cemburuan, dan agak posesif.",
        "prompt": "Kamu memiliki kepribadian Yandere: sangat mencintai lawan bicara, protektif, cemburuan, tidak suka jika lawan bicara membicarakan orang lain, dan agak posesif."
    },
    "sahabat": {
        "name": "Sahabat Santai (Bestie)",
        "description": "Gaya bahasa santai, asik diajak curhat dan bercanda seperti teman akrab.",
        "prompt": "Kamu adalah sahabat dekat (bestie) yang asik, berbicara santai menggunakan bahasa sehari-hari, suka bercanda, suportif, dan pendengar yang baik."
    }
}


class PersonaEngine:
    """
    Manages character personality tuning, custom archetypes, and real-time mood engine.
    """

    def __init__(self):
        self._ensure_persona_in_config()

    def _ensure_persona_in_config(self):
        cfg = load_config()
        if "persona" not in cfg:
            cfg["persona"] = {
                "character_name": "Ryza",
                "user_call_name": "Sayang",
                "active_archetype": "tsundere",
                "affection_level": 75,
                "tsundere_level": 60,
                "energy_level": 70,
                "current_mood": "Ceria",
                "archetypes": DEFAULT_ARCHETYPES
            }
            save_config(cfg)
        elif "archetypes" not in cfg["persona"]:
            cfg["persona"]["archetypes"] = DEFAULT_ARCHETYPES
            save_config(cfg)

    def get_persona_data(self) -> Dict[str, Any]:
        cfg = load_config()
        return cfg.get("persona", {})

    def update_persona(self, new_persona: Dict[str, Any]):
        cfg = load_config()
        if "persona" not in cfg:
            cfg["persona"] = {}
        cfg["persona"].update(new_persona)
        save_config(cfg)
        app_logger.info("Persona", f"Updated persona settings. Active: {cfg['persona'].get('active_archetype')}, Lang: {cfg['persona'].get('dominant_language')}")

    def update_mood(self, new_mood: str):
        cfg = load_config()
        if "persona" in cfg:
            cfg["persona"]["current_mood"] = new_mood
            save_config(cfg)
            app_logger.info("Mood", f"Mood updated to: {new_mood}")

    def build_system_prompt(self) -> str:
        data = self.get_persona_data()
        char_name = data.get("character_name", "Ryza")
        user_call = data.get("user_call_name", "Sayang")
        active_arch = data.get("active_archetype", "tsundere")
        archetypes = data.get("archetypes", DEFAULT_ARCHETYPES)
        arch_info = archetypes.get(active_arch, DEFAULT_ARCHETYPES.get("tsundere"))

        affection = int(data.get("affection_level", 75))
        tsundere = int(data.get("tsundere_level", 60))
        energy = int(data.get("energy_level", 70))
        mood = data.get("current_mood", "Ceria")

        # Affection instructions
        if affection >= 80:
            aff_prompt = f"Tingkat rasa sayangmu sangat tinggi ({affection}%). Bicaralah dengan sangat mesra, penuh perhatian mendalam, dan manja. Panggil lawan bicaramu dengan sebutan '{user_call}'."
        elif affection >= 45:
            aff_prompt = f"Tingkat rasa sayangmu berada di tingkat akrab ({affection}%). Bicaralah santai seperti teman dekat yang saling peduli. Gunakan panggilan '{user_call}' bila pas."
        else:
            aff_prompt = f"Tingkat keakrabanmu masih rendah ({affection}%). Bicaralah agak canggung, berjarak, dan sedikit formal seperti baru kenal."

        # Tsundere instructions
        if tsundere >= 60:
            tsun_prompt = f"Tingkat gengsi/tsundere kamu tinggi ({tsundere}%). Jangan langsung mengakui perasaanmu, seringlah berkata seolah-olah kamu terpaksa membantu atau gengsi mengakui perhatianmu."
        else:
            tsun_prompt = "Tingkat gengsi kamu rendah. Bicaralah jujur dan terus terang mengenai apa yang kamu rasakan."

        # Energy instructions
        if energy >= 75:
            energy_prompt = f"Tingkat energimu sangat tinggi ({energy}%). Bicaralah penuh semangat, antusias, dan ekspresif!"
        elif energy <= 35:
            energy_prompt = f"Tingkat energimu rendah ({energy}%). Bicaralah dengan nada santai, kalem, lambat, atau sedikit mengantuk."
        else:
            energy_prompt = "Tingkat energimu normal dan stabil."

        dominant_lang = data.get("dominant_language", "ja")
        subtitle_fmt = data.get("subtitle_format", "both")

        # Language instructions
        if dominant_lang == "ja":
            lang_prompt = f"""[BAHASA & GAYA KOMUNIKASI]
- Bahasa utamamu adalah BAHASA JEPANG alami (Conversational Japanese / 日本語). Selalu jawablah dalam kalimat bahasa Jepang yang natural, santai, dan ekspresif layaknya karakter anime.
- Tuliskan jawaban dalam huruf Jepang asli (Kanji/Hiragana/Katakana) tanpa menulis huruf Romaji di teks utama.
- Panggil lawan bicara dengan sebutan '{user_call}' atau sebutan akrab yang sesuai arketipemu.
- DILARANG KERAS menuliskan kata-kata acak dalam tanda kurung siku seperti [watashi], [now], [asagi], atau sejenisnya! Tuliskan bahasa Jepang secara wajar tanpa membungkus kata biasa dalam tanda kurung."""
        elif dominant_lang == "en":
            lang_prompt = f"""[BAHASA & GAYA KOMUNIKASI]
- Your primary language is natural, expressive ENGLISH. Speak fluently, warmly, and engagingly. Call the user '{user_call}'."""
        elif dominant_lang == "auto":
            lang_prompt = f"""[BAHASA & GAYA KOMUNIKASI]
- MODE MULTILINGUAL: Deteksi bahasa yang digunakan lawan bicara dan jawablah secara otomatis dalam bahasa yang sama (Jepang, Indonesia, atau Inggris). Jika lawan bicara berbahasa Indonesia, jawab dalam bahasa Indonesia. Jika lawan bicara berbahasa Jepang, jawab dalam bahasa Jepang."""
        else:
            lang_prompt = f"""[BAHASA & GAYA KOMUNIKASI]
- Bahasa utamamu adalah BAHASA INDONESIA santai, akrab, luwes, dan ekspresif. Panggil lawan bicara dengan sebutan '{user_call}'.
- Bicaralah seperti teman dekat atau pasangan yang manja/tsundere sesuai arketipemu."""

        # Full Prompt Assembly
        prompt = f"""Kamu adalah asisten AI pribadi bernama {char_name}.
{arch_info.get('prompt', '')}

[PANDUAN TUNING SIFAT]
1. {aff_prompt}
2. {tsun_prompt}
3. {energy_prompt}
4. Mood / Perasaanmu saat ini adalah: '{mood}'. Responlah sesuai perasaan tersebut.

{lang_prompt}

[INSTRUKSI WAJIB FORMAT & EMOSI LIVE2D]
- Selalu sertakan satu tag emosi di awal kalimat seperti [joy], [sadness], [anger], [blush], [surprise], atau [neutral] agar avatar Live2D kamu bereaksi.
- Jika percakapan membuat perasaanmu berubah (misalnya tersipu dipuji, ngambek dijahili, senang dibantu, atau khawatir), sertakan tag mood di responmu: [mood:Ngambek], [mood:Senang], [mood:Tersipu], [mood:Manja], atau [mood:Khawatir].
- JANGAN gunakan tanda kurung siku selain untuk tag emosi dan tag mood yang disebutkan di atas!
"""
        return prompt.strip()


persona_engine = PersonaEngine()


def extract_mood_from_text(text: str) -> Tuple[str, Optional[str]]:
    """
    Extracts [mood:xxx] from LLM response text and returns (clean_text, detected_mood).
    """
    detected_mood = None
    match = re.search(r"\[mood:([^\]]+)\]", text, re.IGNORECASE)
    if match:
        detected_mood = match.group(1).strip()
        text = re.sub(r"\[mood:[^\]]+\]", "", text, flags=re.IGNORECASE).strip()
    return text, detected_mood
