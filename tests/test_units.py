import unittest
import os
import sys

# Ensure root directory in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.persona import PersonaEngine, extract_mood_from_text
from src.core.interact import InteractEngine
from src.core.proactive import ProactiveEngine
from src.live2d.helper import parse_emotion_and_clean
from src.core.database import Database
from src.core.network import get_windows_host_ip


class TestVTuberCoreUnits(unittest.TestCase):

    def setUp(self):
        self.persona = PersonaEngine()

    def test_persona_archetypes(self):
        """Test persona archetype setting and system prompt generation."""
        for arch in ["tsundere", "deredere", "kuudere", "oneesan", "yandere", "sahabat"]:
            data = self.persona.get_persona_data()
            data["active_archetype"] = arch
            self.persona.update_persona(data)
            self.assertEqual(self.persona.get_persona_data().get("active_archetype"), arch)
            prompt = self.persona.build_system_prompt()
            self.assertIn("Ryza", prompt)
            self.assertIn("INSTRUKSI WAJIB FORMAT & EMOSI LIVE2D", prompt)

    def test_mood_system(self):
        """Test mood setting, modifier generation, and mood tag extraction."""
        self.persona.update_mood("Senang Sekali")
        self.assertEqual(self.persona.get_persona_data().get("current_mood"), "Senang Sekali")

        # Test mood tag extraction
        raw = "Halo user tersayang! [mood:Gembira]"
        clean, mood = extract_mood_from_text(raw)
        self.assertEqual(clean, "Halo user tersayang!")
        self.assertEqual(mood, "Gembira")

        # Reset to Ceria
        self.persona.update_mood("Ceria")
        self.assertEqual(self.persona.get_persona_data().get("current_mood"), "Ceria")

    def test_interact_engine_touch(self):
        """Test touch reactions for headpat, poke, and body across archetypes."""
        for arch in ["tsundere", "deredere", "kuudere", "oneesan", "yandere", "sahabat"]:
            for touch in ["headpat", "poke", "body"]:
                text, tag = InteractEngine.get_touch_reaction(touch, archetype=arch)
                self.assertTrue(len(text) > 0, f"Empty reaction for {arch} {touch}")
                self.assertTrue(len(tag) > 0, f"Invalid tag {tag}")

    def test_proactive_engine(self):
        """Test proactive greeting and wellness reminders."""
        period = ProactiveEngine.get_time_period()
        self.assertIn(period, ["morning", "afternoon", "evening", "late_night"])

        for arch in ["tsundere", "deredere", "kuudere", "oneesan", "yandere", "sahabat"]:
            text, tag = ProactiveEngine.get_greeting(archetype=arch)
            self.assertTrue(len(text) > 0)
            self.assertTrue(len(tag) > 0)

            rem_text, rem_tag = ProactiveEngine.get_break_reminder(archetype=arch)
            self.assertTrue(len(rem_text) > 0)
            self.assertTrue(len(rem_tag) > 0)

    def test_emotion_parser(self):
        """Test emotion tag extraction and Live2D expression mapping."""
        sample_text = "Wah, terima kasih banyak [joy]! *tersenyum*"
        emotion_map = {
            "neutral": 0,
            "smile": 1,
            "joy": 2,
            "blush": 3,
            "pout": 4
        }
        clean, emotion, expr_idx = parse_emotion_and_clean(sample_text, emotion_map)
        self.assertEqual(clean, "Wah, terima kasih banyak!")
        self.assertEqual(emotion, "joy")
        self.assertEqual(expr_idx, 2)

    def test_network_host_ip_detection(self):
        """Test Windows host IP resolution returns valid IP string."""
        host_ip = get_windows_host_ip()
        self.assertIsInstance(host_ip, str)
        self.assertTrue(len(host_ip) >= 7)  # At least 'x.x.x.x'

    def test_database_sqlite(self):
        """Test SQLite message logging and retrieval."""
        test_db_path = "cache/test_unit.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

        db = Database(db_path=test_db_path)
        db.add_message("test_sess", "user", "Halo Ryza!", "[neutral]")
        db.add_message("test_sess", "assistant", "Halo juga sayang!", "[smile]")

        history = db.get_messages("test_sess", limit=5)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")

        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


if __name__ == "__main__":
    unittest.main()
