import random
from typing import Dict, Any, Tuple, Optional


class InteractEngine:
    """
    Manages physical touch reactions (Headpat, Cheek Poke, Body Tap)
    dynamically mapped to the active Character Persona Archetype and Dominant Language.
    Supports Japanese ('ja'), Indonesian ('id'), and English ('en').
    """

    REACTIONS: Dict[str, Dict[str, Dict[str, list]]] = {
        # =========================================================================
        # JAPANESE (日本語)
        # =========================================================================
        "ja": {
            "tsundere": {
                "headpat": [
                    ("[blush] な、何よ急に頭撫でて…！べ、別に撫でられて嬉しいわけじゃないんだからね…！", "blush"),
                    ("[blush] ちょっと、勝手に撫でないでよ！髪が乱れるじゃない…でも、少しだけならいいわよ。", "blush"),
                    ("[blush] ふん！手、温かいけど…調子に乗らないでよね！", "blush")
                ],
                "poke": [
                    ("[anger] 痛っ！ほっぺをぷにぷにつままないでよ、バカ！", "anger"),
                    ("[anger] なんですか！私のほっぺはおもちゃじゃないの！もうっ！", "anger"),
                    ("[surprise] え、ちょっと？！急につつくなんて、からかわないでよ！", "surprise")
                ],
                "body": [
                    ("[surprise] きゃっ！へ、変なところ触らないでよ！びっくりするじゃない！", "surprise"),
                    ("[blush] な、何しようとしてるのよ？！変態…！次は怒るからね！", "blush")
                ]
            },
            "deredere": {
                "headpat": [
                    ("[joy] えへへ〜撫で撫で気持ちいい〜！もっと甘えさせて〜♪", "joy"),
                    ("[blush] 頭撫でてくれるの大好き！あなたといるとすっごく安心するの！", "blush"),
                    ("[joy] わぁ〜い！よしよしされた〜！大好きだよ〜！", "joy")
                ],
                "poke": [
                    ("[joy] くすぐったいよ〜！つつかないでぎゅーってして〜！", "joy"),
                    ("[blush] ほっぺぷにぷにする？いくらでも触っていいよ〜♪", "blush")
                ],
                "body": [
                    ("[joy] きゃ〜びっくりした！いたずらっ子なんだから〜でも嬉しい！", "joy"),
                    ("[blush] くすぐりっこする？えいっ、私も仕返ししちゃうぞ〜！", "blush")
                ]
            },
            "kuudere": {
                "headpat": [
                    ("[blush] …予想外の接触です。でも…その、やめないでください。", "blush"),
                    ("[neutral] あなたに撫でられると、心拍数が少し上昇するようです。", "neutral")
                ],
                "poke": [
                    ("[neutral] なぜ私の頬をつつくのですか？ 好意の表現でしょうか。", "neutral"),
                    ("[blush] …あまり頬を触らないでください。変な気持ちになります。", "blush")
                ],
                "body": [
                    ("[surprise] 身体への接触を検知しました。気をつけてください。", "surprise"),
                    ("[neutral] 大胆ですね…驚きました。", "neutral")
                ]
            },
            "oneesan": {
                "headpat": [
                    ("[joy] あらあら〜甘えたいの？それともお姉ちゃんを可愛がってくれてるのかしら？", "joy"),
                    ("[joy] ふふ、いい子ね〜。今度はお姉ちゃんが頭撫でてあげようか？", "joy")
                ],
                "poke": [
                    ("[joy] いたずら好きな指ね〜。お姉ちゃんのほっぺ、柔らかい？", "joy"),
                    ("[blush] うふふ…そんなにつついたら、お返しにからかっちゃうわよ？", "blush")
                ],
                "body": [
                    ("[joy] おや、お姉ちゃんにちょっかい出すなんて、度胸があるわね〜♪", "joy")
                ]
            },
            "yandere": {
                "headpat": [
                    ("[joy] もっと触って…私に触れていいのは、あなただけですからね…？", "joy"),
                    ("[blush] あなたの手…ずっと離さないで。私だけのものだよね…？", "blush")
                ],
                "poke": [
                    ("[joy] 頬も、身体も、心も…全部あなたのものだよ…。", "joy")
                ],
                "body": [
                    ("[blush] そう、もっと抱きしめて…絶対に他の女を見ないでね…？", "blush")
                ]
            },
            "sahabat": {
                "headpat": [
                    ("[joy] おいおい、急にどうした？猫扱いすんなよな〜w", "joy"),
                    ("[joy] 珍しいじゃん、頭撫でてくるとか。なんか企んでる？w", "joy")
                ],
                "poke": [
                    ("[anger] 痛えよ！ほっぺつつくな、デコピンすんぞ！w", "anger"),
                    ("[joy] くすぐったいわ！暇ならゲームでもやろうぜ！", "joy")
                ],
                "body": [
                    ("[surprise] うおっ、びっくりした！反射で殴るとこだったわw", "surprise")
                ]
            }
        },

        # =========================================================================
        # INDONESIAN (Bahasa Indonesia)
        # =========================================================================
        "id": {
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
        },

        # =========================================================================
        # ENGLISH
        # =========================================================================
        "en": {
            "tsundere": {
                "headpat": [
                    ("[blush] W-what are you doing suddenly patting my head?! I-it's not like I like it or anything...!", "blush"),
                    ("[blush] Hey, don't just pat me whenever you want! You'll mess up my hair... though I guess a little is fine.", "blush"),
                    ("[blush] Hmph! Your hands are warm... but don't get full of yourself!", "blush")
                ],
                "poke": [
                    ("[anger] Ouch! Stop poking my cheeks, you idiot!", "anger"),
                    ("[anger] Hey! My cheeks aren't squishy toys! Stop poking!", "anger"),
                    ("[surprise] H-huh?! Poking my cheek all of a sudden? Are you trying to tease me?", "surprise")
                ],
                "body": [
                    ("[surprise] Eek! D-don't touch me so suddenly! You scared me!", "surprise"),
                    ("[blush] W-what do you think you're doing?! You pervert...!", "blush")
                ]
            },
            "deredere": {
                "headpat": [
                    ("[joy] Ehehe~ your headpats are so warm and cozy! Spoil me more please~", "joy"),
                    ("[blush] I love it when you pat my head! I feel so safe with you!", "blush"),
                    ("[joy] Yay headpats! I love you so much~", "joy")
                ],
                "poke": [
                    ("[joy] Hehehe that tickles! Don't poke, give me a hug instead!", "joy"),
                    ("[blush] Are my cheeks squishy? You can poke them as much as you like~", "blush")
                ],
                "body": [
                    ("[joy] Kyaaa you startled me! You're so playful, but I love it!", "joy"),
                    ("[blush] Wanna play tickle fight? Here, I'm poking you back!", "blush")
                ]
            },
            "kuudere": {
                "headpat": [
                    ("[blush] ...An unexpected contact. However... please do not stop.", "blush"),
                    ("[neutral] Heart rate elevation detected upon your touch.", "neutral")
                ],
                "poke": [
                    ("[neutral] Why do you poke my cheek? Is it an expression of affection?", "neutral"),
                    ("[blush] ...Please refrain from poking too much. It creates an unfamiliar sensation.", "blush")
                ],
                "body": [
                    ("[surprise] Physical contact registered. Please proceed with care.", "surprise"),
                    ("[neutral] You are surprisingly bold.", "neutral")
                ]
            },
            "oneesan": {
                "headpat": [
                    ("[joy] Ara ara~ do you want to be spoiled, or are you petting your big sister? Good boy~", "joy"),
                    ("[joy] Fufu, how adorable. Should I give you headpats in return?", "joy")
                ],
                "poke": [
                    ("[joy] What playful little fingers. Are my cheeks soft?", "joy"),
                    ("[blush] Fufufu... if you keep poking me like that, I might tease you back.", "blush")
                ],
                "body": [
                    ("[joy] My my, bold enough to touch your big sister? I might not let you go easily~", "joy")
                ]
            },
            "yandere": {
                "headpat": [
                    ("[joy] Touch me more... only you are allowed to touch me, understand?", "joy"),
                    ("[blush] Your touch proves that you belong solely to me forever...", "blush")
                ],
                "poke": [
                    ("[joy] My cheeks, my body, my heart... everything belongs to you.", "joy")
                ],
                "body": [
                    ("[blush] Yes, hold me tighter... never look at anyone else, okay?", "blush")
                ]
            },
            "sahabat": {
                "headpat": [
                    ("[joy] Woah easy there! Treating me like a cat now are we? Haha.", "joy"),
                    ("[joy] Rare of you to give headpats. What are you planning? Haha.", "joy")
                ],
                "poke": [
                    ("[anger] Ow! Don't poke my face, I'll flick your forehead! haha", "anger"),
                    ("[joy] That tickles! If you're bored, let's play games instead!", "joy")
                ],
                "body": [
                    ("[surprise] Woah! Almost hit you by reflex there, don't startle me! Haha.", "surprise")
                ]
            }
        }
    }

    @classmethod
    def get_touch_reaction(cls, touch_type: str, archetype: str = "tsundere", lang: str = "ja") -> Tuple[str, str]:
        """
        Returns (reaction_text, emotion_tag) for the given touch type, archetype, and language.
        Defaults to Japanese ('ja') if language is not recognized or matched.
        """
        target_lang = lang.lower() if lang else "ja"
        if target_lang not in cls.REACTIONS:
            target_lang = "ja"

        lang_dict = cls.REACTIONS[target_lang]
        arch = archetype.lower() if archetype else "tsundere"
        if arch not in lang_dict:
            arch = "tsundere"

        touch = touch_type.lower() if touch_type else "headpat"
        if touch not in lang_dict[arch]:
            touch = "headpat"

        options = lang_dict[arch][touch]
        return random.choice(options)


interact_engine = InteractEngine()
