import os
import sys
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.tts.base import BaseTTSProvider


class KokoroTTSProvider(BaseTTSProvider):
    """
    Kokoro-82M Local Neural TTS Provider.
    Produces high-fidelity neural speech with natural inflection.
    """

    DEFAULT_VOICES = [
        {"id": "jf_alpha", "name": "Kokoro Alpha (Jepang Anime - Tsundere/Ekspresif)", "lang": "ja-JP"},
        {"id": "jf_tebukuro", "name": "Kokoro Tebukuro (Jepang Anime - Lembut)", "lang": "ja-JP"},
        {"id": "jf_gongitsune", "name": "Kokoro Gongitsune (Jepang Anime - Ceria)", "lang": "ja-JP"},
        {"id": "jf_nezumi", "name": "Kokoro Nezumi (Jepang Anime - Imut)", "lang": "ja-JP"},
        {"id": "af_heart", "name": "Kokoro Heart (Inggris - Alami & Jernih)", "lang": "en-US"}
    ]

    def __init__(self, config: Dict[str, Any], cache_dir: str):
        super().__init__("kokoro", "Kokoro-82M Neural TTS", config, cache_dir)
        self.worker_script = str(Path(__file__).parent / "kokoro_worker.py")

    def _get_python_path(self) -> str:
        configured_path = self.config.get("python_path", "").strip()
        if configured_path and os.path.isfile(configured_path):
            return configured_path

        # Check default WSL location for kokoro-arch
        kokoro_arch_venv = "/home/hideri/coding/kokoro-arch/.venv/bin/python3"
        if os.path.isfile(kokoro_arch_venv):
            return kokoro_arch_venv

        return sys.executable

    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        emotion: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        if not text or not text.strip():
            return None

        chosen_voice = voice or self.config.get("default_voice", "jf_alpha")
        speed = float(self.config.get("speed", 1.0))
        lang = self.config.get("lang_code", "")

        file_id = f"kokoro_{uuid.uuid4().hex[:12]}.wav"
        file_path = os.path.join(self.cache_dir, file_id)
        python_bin = self._get_python_path()

        cmd = [
            python_bin,
            self.worker_script,
            "--text", text.strip(),
            "--voice", chosen_voice,
            "--speed", str(speed),
            "--output", file_path
        ]
        if lang:
            cmd.extend(["--lang", lang])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0 and os.path.exists(file_path):
                return file_path

            err_msg = stderr.decode().strip() or stdout.decode().strip()
            print(f"[KokoroTTSProvider] Synthesis failed (code {process.returncode}): {err_msg}")
            return None
        except Exception as e:
            print(f"[KokoroTTSProvider] Subprocess execution error: {e}")
            return None

    def get_available_voices(self) -> List[Dict[str, str]]:
        configured_voices = self.config.get("available_voices")
        if configured_voices and isinstance(configured_voices, list):
            return configured_voices
        return self.DEFAULT_VOICES

    async def is_available(self) -> bool:
        python_bin = self._get_python_path()
        if not os.path.isfile(python_bin):
            return False

        try:
            proc = await asyncio.create_subprocess_exec(
                python_bin, "-c", "import kokoro; print('ok')",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return b"ok" in stdout
        except Exception:
            return False
