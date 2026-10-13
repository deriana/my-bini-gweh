"""
Romanization and Phonetic Transliteration Engine for Bilingual & Multilingual VTubers.
Handles:
1. Japanese -> Romaji conversion (using pykakasi) for subtitles/display.
2. Latin (Indonesian/English) -> Katakana phonetic conversion (using jaconv) for single-language Japanese TTS engines like VOICEVOX.
"""

import re
from typing import Optional
import jaconv
import pykakasi

# Singleton kakasi converter
_kakasi = pykakasi.kakasi()

# Common English/Indo to Japanese phonetic dictionary for smooth VOICEVOX pronunciation
PHONETIC_REPLACEMENTS = {
    # English common words
    r"\bhello\b": "hero",
    r"\bhi\b": "hai",
    r"\bhey\b": "hei",
    r"\bwhat\b": "hwatto",
    r"\bhow\b": "hau",
    r"\bwhere\b": "hwea",
    r"\bwhy\b": "hwai",
    r"\byou\b": "yuu",
    r"\bmy\b": "mai",
    r"\bme\b": "mii",
    r"\bare\b": "aa",
    r"\bis\b": "izu",
    r"\bam\b": "amu",
    r"\btoday\b": "todei",
    r"\bgood\b": "guddo",
    r"\bmorning\b": "mooningu",
    r"\bnight\b": "naito",
    r"\bfriend\b": "furendo",
    r"\bthanks\b": "sankusu",
    r"\bthank you\b": "sankyuu",
    r"\bplease\b": "puriizu",
    r"\bsorry\b": "sorii",
    r"\byes\b": "iesu",
    r"\bno\b": "nou",
    r"\blove\b": "rabu",
    r"\blike\b": "raiku",
    r"\bcool\b": "kuuru",
    r"\bcute\b": "kyuuto",
    r"\bstream\b": "sutoriimu",
    r"\bgame\b": "geemu",
    r"\bplay\b": "purei",
    r"\bcode\b": "koudo",
    r"\bcoding\b": "koudingu",
    r"\bvtuber\b": "bityuubaa",
    r"\bai\b": "eeai",
    # Indonesian common honorifics & words
    r"\bgue\b": "gue",
    r"\blu\b": "lu",
    r"\bwkwk\b": "wkwk",
}


def contains_japanese(text: str) -> bool:
    """Checks if text contains Japanese script (Hiragana, Katakana, or Kanji)."""
    if not text:
        return False
    return bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", text))


def to_romaji(text: str) -> str:
    """
    Converts Japanese text (Kanji, Hiragana, Katakana) into clean, natural Hepburn Romaji.
    Example: 'おはようございます、ご主人様！' -> 'Ohayougozaimasu, go shujinsama!'
    """
    if not text:
        return ""
    try:
        conv = _kakasi.convert(text)
        parts = [item.get("hepburn", "") for item in conv]
        res = " ".join(parts)
        # Normalize punctuation spacing
        res = re.sub(r"\s+([,.!?])", r"\1", res)
        res = re.sub(r"\s+", " ", res).strip()

        # Fix common Japanese particle pronunciation (ha -> wa for greetings and topic marker)
        res = re.sub(r"\bkonnichiha\b", "konnichiwa", res, flags=re.IGNORECASE)
        res = re.sub(r"\bkonbanha\b", "konbanwa", res, flags=re.IGNORECASE)
        res = re.sub(r"\s+ha\s+", " wa ", res, flags=re.IGNORECASE)

        # Capitalize beginning of sentences
        sentences = re.split(r"([.!?]\s*)", res)
        formatted = "".join(
            [s.capitalize() if not re.match(r"^[.!?]\s*$", s) else s for s in sentences]
        )
        return formatted
    except Exception as e:
        print(f"[Romanize] Error converting to romaji: {e}")
        return text


def format_display_text(clean_text: str, subtitle_format: str = "both") -> str:
    """
    Formats text for speech bubble / subtitles based on subtitle format:
    - 'both': Shows original Japanese + (Romaji) underneath
    - 'japanese_only': Shows only Japanese
    - 'romaji_only': Shows only Romaji
    If text does not contain Japanese, returns original text unchanged.
    """
    if not clean_text:
        return ""

    if not contains_japanese(clean_text):
        return clean_text

    romaji = to_romaji(clean_text)
    if not romaji:
        return clean_text

    if subtitle_format == "romaji_only":
        return romaji
    elif subtitle_format == "japanese_only":
        return clean_text
    else:
        # Default: 'both' -> Japanese with Romaji underneath
        return f"{clean_text}\n({romaji})"


def latin_to_japanese_phonetic(text: str) -> str:
    """
    Transliterates Latin alphabet (Indonesian/English) into Katakana phonetics.
    Used for single-language Japanese TTS engines (VOICEVOX) so they pronounce foreign words
    smoothly with cute Japanese accents rather than skipping or butchering them.
    Example: 'selamat pagi apa kabar' -> 'セラマト パギ アパ カバル'
    """
    if not text or not text.strip():
        return ""

    t = text.lower().strip()

    # 1. Apply phonetic vocabulary mappings
    for pattern, rep in PHONETIC_REPLACEMENTS.items():
        t = re.sub(pattern, rep, t, flags=re.IGNORECASE)

    # 2. Epenthetic vowel insertion for trailing consonants (Indonesian & English closed syllables)
    coda_vowel_map = {
        "t": "to", "d": "do", "k": "ku", "g": "gu", "p": "pu", "b": "bu",
        "s": "su", "z": "zu", "r": "ru", "l": "ru", "m": "mu", "f": "fu",
        "v": "bu", "h": "h", "n": "n", "j": "ji", "c": "ku"
    }
    t = re.sub(r"([bcdfghjklmnpqrstvwxyz])\b", lambda m: coda_vowel_map.get(m.group(1), m.group(1)), t)

    # 3. Handle double consonants or consonant clusters
    t = re.sub(r"([bcdfghjklpqrstvwxz])([bcdfghjklpqrstvwxz])", lambda m: m.group(1) + ("o" if m.group(1) in "td" else "u") + m.group(2), t)

    # 4. Convert alphabet to Katakana via jaconv
    try:
        kana = jaconv.hira2kata(jaconv.alphabet2kana(t))
        return kana
    except Exception as e:
        print(f"[Romanize] Error converting Latin to Katakana: {e}")
        return text


def prepare_for_voicevox(text: str) -> str:
    """
    Prepares any text for VOICEVOX speech synthesis:
    - If text is pure Japanese: returns as is.
    - If text is mixed (Japanese + English/Latin words): transliterates Latin words to Katakana while keeping Japanese.
    - If text is Latin only (Indonesian / English): transliterates entirely into Katakana phonetics.
    """
    if not text or not text.strip():
        return ""

    has_jp = contains_japanese(text)
    has_latin = bool(re.search(r"[a-zA-Z]", text))

    if has_jp and not has_latin:
        # Pure Japanese
        return text.strip()

    if not has_jp:
        # Pure Latin (Indonesian / English)
        return latin_to_japanese_phonetic(text)

    # Mixed text: replace Latin words inside Japanese sentence with Katakana
    def _replace_word(m):
        word = m.group(0)
        return latin_to_japanese_phonetic(word)

    return re.sub(r"[a-zA-Z]+", _replace_word, text)
