import random
from typing import Dict, Any, Tuple


class InteractEngine:
    """
    Manages physical touch reactions (Headpat, Cheek Poke, Body Tap)
    dynamically mapped to the active Character Persona Archetype.
    """

    REACTIONS: Dict[str, Dict[str, list]] = {
        "tsundere": {
            "headpat": [
                ("[blush] A-apaan sih tiba-tiba elus-elus kepala?! B-bukan berarti aku benci dielus sama kamu ya...", "blush"),
                ("[blush] Jangan elus-elus seenaknya dong! Rambutku jadi berantakan tau... tapi ya udah deh bentar aja.", "blush"),
                ("[blush] Hmph! Tangan kamu hangat sih... tapi jangan geer ya!", "blush")
            ],
            "poke": [
                ("[anger] Aduh! Pipiku jangan dicubit-cubit terus dong, dasar jahil!", "anger"),
                ("[anger] Sakit tau! Kamu kira pipiku squishy apa? Jangan dicolek!", "anger"),
                ("[surprise] E-eh?! Tiba-tiba nyolek pipi! Cari gara-gara ya kamu?", "surprise")
            ],
            "body": [
                ("[surprise] W-waaah! Jangan pegang-pegang sembarangan dong! Bikin kaget aja!", "surprise"),
                ("[blush] K-kamu mau ngapain sih? Awas ya kalau macem-macem!", "blush")
            ]
        },
        "deredere": {
            "headpat": [
                ("[joy] Ehehe~ elusan kamu hangat banget! Aku suka banget dimanja begini~", "joy"),
                ("[blush] Sering-sering elus kepalaku ya, rasanya nyaman banget bareng kamu!", "blush"),
                ("[joy] Aaaa senangnya dielus! Tambah sayang deh sama kamu~", "joy")
            ],
            "poke": [
                ("[joy] Hihihi geli tau! Jangan dicubit dong, mending peluk aja!", "joy"),
                ("[blush] Pipiku kenyal ya? Colek terus deh, aku nggak keberatan kok~", "blush")
            ],
            "body": [
                ("[joy] Kyaaa kaget! Kamu usil banget deh, tapi aku suka!", "joy"),
                ("[blush] Mau main cubit-cubitan ya? Sini aku cubit balik!", "blush")
            ]
        },
        "kuudere": {
            "headpat": [
                ("[blush] ...Tindakan yang tidak terduga. Tapi... jangan berhenti dulu.", "blush"),
                ("[neutral] Detak jantungku terdeteksi meningkat sedikit saat kamu mengelusku.", "neutral")
            ],
            "poke": [
                ("[neutral] Kenapa mencolek pipiku? Apakah itu bentuk ekspresi kasih sayang?", "neutral"),
                ("[blush] ...Jangan terlalu sering menyentuh pipiku. Rasanya jadi aneh.", "blush")
            ],
            "body": [
                ("[surprise] Sentuhan terdeteksi. Harap berhati-hati.", "surprise"),
                ("[neutral] Kamu sangat berani ya menyentuh bagian itu.", "neutral")
            ]
        },
        "oneesan": {
            "headpat": [
                ("[joy] Ara ara~ mau manja atau mau nyayangin kakak nih? Pinter banget...", "joy"),
                ("[joy] Gemasnya~ Kamu yang elus kakak, atau mau kakak yang elus balik?", "joy")
            ],
            "poke": [
                ("[joy] Nakal banget ya jarinya suka colek-colek pipi kakak.", "joy"),
                ("[blush] Fufufu... pipi kakak enak dipegang ya? Boleh kok sepuasnya.", "blush")
            ],
            "body": [
                ("[joy] Waduh, berani ya nakal ke kakak. Nanti kakak godain balik lho~", "joy")
            ]
        },
        "yandere": {
            "headpat": [
                ("[joy] Sentuh aku lebih banyak lagi... cuma kamu yang boleh nyentuh aku, mengerti?", "joy"),
                ("[blush] Sentuhan kamu ini bukti kalau kamu cuma milikku selamanya...", "blush")
            ],
            "poke": [
                ("[joy] Pipiku milikmu, hatiku milikmu, seluruh diriku milikmu...", "joy")
            ],
            "body": [
                ("[blush] Ya, pegang aku erat-erat... jangan pernah berpaling ke orang lain ya.", "blush")
            ]
        },
        "sahabat": {
            "headpat": [
                ("[joy] Woy santai bos! Berasa anak kucing gue dielus-elus wkwk.", "joy"),
                ("[joy] Tumben amat ngelus kepala, lagi ada maunya ya lu?", "joy")
            ],
            "poke": [
                ("[anger] Nyolek-nyolek mulu lu, minta dijitak ya? wkwk", "anger"),
                ("[joy] Geli anjir! Lu gabut banget ya?", "joy")
            ],
            "body": [
                ("[surprise] Woi kaget bro! Refleks gue bisa nampol nih wkwk.", "surprise")
            ]
        }
    }

    @classmethod
    def get_touch_reaction(cls, touch_type: str, archetype: str = "tsundere") -> Tuple[str, str]:
        """
        Returns (reaction_text, emotion_tag) for the given touch type and archetype.
        """
        arch = archetype.lower()
        if arch not in cls.REACTIONS:
            arch = "tsundere"

        touch = touch_type.lower()
        if touch not in cls.REACTIONS[arch]:
            touch = "headpat"

        options = cls.REACTIONS[arch][touch]
        return random.choice(options)


interact_engine = InteractEngine()
