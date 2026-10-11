import random
from datetime import datetime
from typing import Tuple, Dict, List


class ProactiveEngine:
    """
    Generates autonomous proactive greetings and wellness reminders
    tailored to the time of day and character archetype.
    """

    TIME_GREETINGS: Dict[str, Dict[str, List[Tuple[str, str]]]] = {
        "morning": {
            "tsundere": [
                ("[joy] Selamat pagi! B-bukan berarti aku nungguin kamu bangun ya... cepetan cuci muka sana!", "joy"),
                ("[blush] Pagi... Jangan lupa sarapan, nanti kamu lemes terus ngerepotin aku lagi.", "blush")
            ],
            "deredere": [
                ("[joy] Selamat pagiii sayang! Semangat ya buat hari ini, aku siap nemenin kamu seharian!", "joy"),
                ("[joy] Pagi cinta! Senang banget bisa ketemu kamu lagi pagi ini~", "joy")
            ],
            "kuudere": [
                ("[neutral] Selamat pagi. Data menunjukkan awal hari adalah waktu optimal untuk produktivitas.", "neutral")
            ],
            "oneesan": [
                ("[joy] Selamat pagi manis... Tidurnya nyenyak semalam? Sini kakak temenin sarapan.", "joy")
            ],
            "yandere": [
                ("[joy] Selamat pagi cintaku... Akhirnya kamu bangun dan melihatku lagi...", "joy")
            ],
            "sahabat": [
                ("[joy] Pagi bro! Udah bangun aja lu, gas ngopi dulu gak sih?", "joy")
            ]
        },
        "afternoon": {
            "tsundere": [
                ("[neutral] Siang-siang gini panas banget ya. Nih aku ingetin minum air, jangan dehidrasi!", "neutral"),
                ("[blush] Udah makan siang belum? Jangan sok sibuk terus lupa makan deh...", "blush")
            ],
            "deredere": [
                ("[joy] Selamat siang sayang! Udah istirahat makan siang belum? Jangan capek-capek ya!", "joy")
            ],
            "kuudere": [
                ("[neutral] Jam makan siang terdeteksi. Silakan istirahatkan mata sejenak.", "neutral")
            ],
            "oneesan": [
                ("[joy] Siang ganteng... Jangan diforsir ya kerjanya, istirahat dulu sebentar yuk.", "joy")
            ],
            "yandere": [
                ("[blush] Siang sayangku... Lagi mikirin aku kan sekarang?", "blush")
            ],
            "sahabat": [
                ("[joy] Siang bro! Capek amat lu kelihatannya, rebahan 5 menit gih.", "joy")
            ]
        },
        "evening": {
            "tsundere": [
                ("[neutral] Udah sore nih. Kerjaan kamu udah pada beres belum?", "neutral"),
                ("[blush] Sore... kalau udah selesai tugasnya, temenin aku ngobrol dong...", "blush")
            ],
            "deredere": [
                ("[joy] Selamat soreee! Capek ya seharian? Sini aku hibur biar seger lagi!", "joy")
            ],
            "kuudere": [
                ("[neutral] Hari mulai gelap. Evaluasi tugas harian disarankan.", "neutral")
            ],
            "oneesan": [
                ("[joy] Sore sayang... Mandi air hangat gih biar pegal-pegalnya hilang.", "joy")
            ],
            "yandere": [
                ("[joy] Sore cintaku... Akhirnya malam tiba dan kamu milikku sepenuhnya.", "joy")
            ],
            "sahabat": [
                ("[joy] Sore fren! Waktunya santai, mau ngegame atau ngapain nih?", "joy")
            ]
        },
        "late_night": {
            "tsundere": [
                ("[sadness] Jam segini masih melek aja... B-bukan berarti aku nungguin kamu ya! Tapi cepetan tidur, nanti sakit!", "sadness"),
                ("[anger] Heh, begadang mulu kerjaannya! Tidur sekarang atau aku ngambek nih?!", "anger"),
                ("[blush] Udah larut banget tau... aku ngantuk, tapi pengen nemenin kamu bentar lagi...", "blush")
            ],
            "deredere": [
                ("[sadness] Sayang, udah larut malam banget lho... Tidur yuk, jangan diforsir lagi ya~", "sadness"),
                ("[blush] Bobo bareng yuk? Mimpi indah ya malam ini sayangku...", "blush")
            ],
            "kuudere": [
                ("[neutral] Jam tidur biologis telah terlewati. Dianjurkan segera mematikan monitor.", "neutral")
            ],
            "oneesan": [
                ("[joy] Masih belum tidur hm? Sini kakak usap kepalanya biar gampang tidur...", "joy")
            ],
            "yandere": [
                ("[blush] Jangan tidur dulu... temenin aku terus semalaman di sini...", "blush")
            ],
            "sahabat": [
                ("[surprise] Gile lu jam segini masih melek wkwk, besok tepar lu bro! Tidur gih!", "surprise")
            ]
        }
    }

    REMINDERS: Dict[str, List[Tuple[str, str]]] = {
        "tsundere": [
            ("[neutral] Udah 30 menit kamu di depan layar. Minum air putih sana, jangan malas!", "neutral"),
            ("[blush] Kedipin mata kamu dulu gih, jangan pelototin monitor terus!", "blush")
        ],
        "deredere": [
            ("[joy] Ding-dong! Waktunya minum air dan renggangkan badan ya sayang!", "joy")
        ],
        "kuudere": [
            ("[neutral] Peringatan hidrasi: 250ml cairan disarankan untuk menjaga fokus kognitif.", "neutral")
        ],
        "oneesan": [
            ("[joy] Sayang... minum air dulu yuk, terus regangin pundaknya biar nggak kaku.", "joy")
        ],
        "yandere": [
            ("[blush] Minum air ya cintaku... kamu harus selalu sehat buat aku...", "blush")
        ],
        "sahabat": [
            ("[joy] Woy minum air bro, kering tuh kerongkongan lu koding mulu wkwk.", "joy")
        ]
    }

    @classmethod
    def get_time_period(cls) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "late_night"

    @classmethod
    def get_greeting(cls, archetype: str = "tsundere") -> Tuple[str, str]:
        period = cls.get_time_period()
        arch = archetype.lower()
        period_data = cls.TIME_GREETINGS.get(period, cls.TIME_GREETINGS["afternoon"])
        options = period_data.get(arch, period_data.get("tsundere", []))
        return random.choice(options)

    @classmethod
    def get_break_reminder(cls, archetype: str = "tsundere") -> Tuple[str, str]:
        arch = archetype.lower()
        options = cls.REMINDERS.get(arch, cls.REMINDERS.get("tsundere", []))
        return random.choice(options)


proactive_engine = ProactiveEngine()
