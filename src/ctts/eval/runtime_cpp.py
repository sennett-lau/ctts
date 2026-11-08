"""Native qwen3-tts.cpp (libqwen3_tts_shared.so) ctypes wrapper & punctuation chunker.

Supports:
  - Named CustomVoice synthesis (`synthesize`)
  - Zero-shot WAV voice cloning (`synthesize_with_voice`)
  - Zero-shot `.spk` speaker-embedding synthesis & extraction (`extract_speaker_embedding`, `synthesize_with_spk`)
  - Full `.icl` emotion/prosody prompt extraction & synthesis (`extract_icl_prompt`, `synthesize_with_icl`)
  - Punctuation chunking (<= 42 chars) to prevent Qwen3-TTS 12Hz long-sentence clause skipping.
"""

from __future__ import annotations

import ctypes
import io
import re
import struct
import threading
import time
from pathlib import Path


class _Params(ctypes.Structure):
    _fields_ = [
        ("max_audio_tokens", ctypes.c_int32),
        ("temperature", ctypes.c_float),
        ("top_p", ctypes.c_float),
        ("top_k", ctypes.c_int32),
        ("n_threads", ctypes.c_int32),
        ("print_progress", ctypes.c_int32),
        ("print_timing", ctypes.c_int32),
        ("repetition_penalty", ctypes.c_float),
        ("language_id", ctypes.c_int32),
        ("instruction", ctypes.c_char_p),
        ("speaker", ctypes.c_char_p),
        ("vocoder_left_context_sec", ctypes.c_float),
    ]


class _Result(ctypes.Structure):
    _fields_ = [
        ("audio", ctypes.POINTER(ctypes.c_float)),
        ("audio_len", ctypes.c_int32),
        ("sample_rate", ctypes.c_int32),
        ("success", ctypes.c_int32),
        ("error_msg", ctypes.c_char_p),
        ("t_total_ms", ctypes.c_int64),
    ]


def split_chunks(text: str, max_chars: int = 42) -> list[str]:
    """Split text at punctuation into chunks of <= max_chars (prevents >45 char clause skipping)."""
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    parts = re.split(r"(?<=[。！？!?；;，,、：\n])", text)
    chunks, cur = [], ""
    for p in parts:
        if not p:
            continue
        if len(cur) + len(p) <= max_chars:
            cur += p
        else:
            if cur:
                chunks.append(cur.strip())
            while len(p) > max_chars:
                chunks.append(p[:max_chars].strip())
                p = p[max_chars:]
            cur = p
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def pcm16_to_wav(pcm: bytes, sr: int = 24000) -> bytes:
    buf = io.BytesIO()
    n = len(pcm)
    buf.write(
        b"RIFF"
        + struct.pack("<I", 36 + n)
        + b"WAVEfmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16)
        + b"data"
        + struct.pack("<I", n)
        + pcm
    )
    return buf.getvalue()


class Qwen3TTSCppEngine:
    """Thread-safe resident wrapper around qwen3-tts.cpp's C ABI."""

    def __init__(self, build_dir: Path, model_dir: Path, model_name: str, threads: int = 16):
        self.build_dir = Path(build_dir)
        self.model_dir = Path(model_dir)
        self.model_name = model_name
        self.threads = threads
        self._lock = threading.Lock()

        for so in ("libggml-base.so", "libggml-cpu.so", "libggml.so"):
            p = self.build_dir / "ggml/src" / so
            if p.exists():
                ctypes.CDLL(str(p), mode=ctypes.RTLD_GLOBAL)
        self._lib = ctypes.CDLL(str(self.build_dir / "libqwen3_tts_shared.so"))
        self._bind()

        self._lib.qwen3_tts_set_cpu_threads(self.threads)
        self._ctx = self._lib.qwen3_tts_init()
        if not self._lib.qwen3_tts_load_models_with_name(
            self._ctx, str(self.model_dir).encode(), self.model_name.encode()
        ):
            raise RuntimeError(f"Failed to load GGUF model {self.model_name} from {self.model_dir}")

    def _bind(self):
        L = self._lib
        L.qwen3_tts_init.restype = ctypes.c_void_p
        L.qwen3_tts_set_cpu_threads.argtypes = [ctypes.c_int32]
        L.qwen3_tts_load_models_with_name.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        L.qwen3_tts_load_models_with_name.restype = ctypes.c_int32
        L.qwen3_tts_synthesize.argtypes = [ctypes.c_void_p, ctypes.c_char_p, _Params]
        L.qwen3_tts_synthesize.restype = _Result
        L.qwen3_tts_synthesize_with_voice.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, _Params]
        L.qwen3_tts_synthesize_with_voice.restype = _Result
        L.qwen3_tts_synthesize_with_speaker_embedding.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, _Params
        ]
        L.qwen3_tts_synthesize_with_speaker_embedding.restype = _Result
        L.qwen3_tts_synthesize_with_icl_prompt.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, _Params
        ]
        L.qwen3_tts_synthesize_with_icl_prompt.restype = _Result
        L.qwen3_tts_extract_speaker_embedding.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        L.qwen3_tts_extract_speaker_embedding.restype = ctypes.c_int32
        L.qwen3_tts_extract_icl_prompt.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p
        ]
        L.qwen3_tts_extract_icl_prompt.restype = ctypes.c_int32
        L.qwen3_tts_get_available_speakers.argtypes = [ctypes.c_void_p]
        L.qwen3_tts_get_available_speakers.restype = ctypes.c_char_p
        L.qwen3_tts_free_result.argtypes = [_Result]

    def speakers(self) -> list[str]:
        raw = self._lib.qwen3_tts_get_available_speakers(self._ctx)
        return [s for s in (raw.decode() if raw else "").splitlines() if s]

    def extract_speaker_embedding(self, ref_wav: Path, out_spk: Path) -> bool:
        with self._lock:
            return bool(
                self._lib.qwen3_tts_extract_speaker_embedding(self._ctx, str(ref_wav).encode(), str(out_spk).encode())
            )

    def extract_icl_prompt(self, ref_wav: Path, ref_text: str, out_icl: Path) -> bool:
        with self._lock:
            return bool(
                self._lib.qwen3_tts_extract_icl_prompt(
                    self._ctx, str(ref_wav).encode(), ref_text.encode("utf-8"), str(out_icl).encode()
                )
            )

    def synthesize_pcm16(
        self,
        text: str,
        speaker: str = "hk_voice_343",
        instruction: str | None = None,
        ref_wav: Path | None = None,
        spk_file: Path | None = None,
        icl_file: Path | None = None,
        language_id: int = 2055,
        temperature: float = 0.9,
        top_k: int = 50,
        top_p: float = 1.0,
        rep_pen: float = 1.05,
        max_chars: int = 42,
    ) -> tuple[bytes, int, float]:
        chunks = split_chunks(text, max_chars=max_chars)
        if not chunks:
            return b"", 24000, 0.0
        pcm_parts = []
        sr = 24000
        t0 = time.time()
        inst_b = instruction.encode("utf-8") if instruction else None
        spk_b = speaker.encode("utf-8") if (speaker and not ref_wav and not spk_file and not icl_file) else None
        with self._lock:
            for ch in chunks:
                p = _Params(
                    2048, float(temperature), float(top_p), int(top_k), self.threads,
                    0, 0, float(rep_pen), int(language_id), inst_b, spk_b, 0.0
                )
                ch_b = ch.encode("utf-8")
                if icl_file:
                    res = self._lib.qwen3_tts_synthesize_with_icl_prompt(self._ctx, ch_b, str(icl_file).encode(), p)
                elif spk_file:
                    res = self._lib.qwen3_tts_synthesize_with_speaker_embedding(self._ctx, ch_b, str(spk_file).encode(), p)
                elif ref_wav:
                    res = self._lib.qwen3_tts_synthesize_with_voice(self._ctx, ch_b, str(ref_wav).encode(), p)
                else:
                    res = self._lib.qwen3_tts_synthesize(self._ctx, ch_b, p)
                try:
                    if res.success and res.audio_len > 0:
                        sr = res.sample_rate or 24000
                        arr = (ctypes.c_float * res.audio_len).from_address(ctypes.addressof(res.audio.contents))
                        pcm = bytearray(res.audio_len * 2)
                        for i, v in enumerate(arr):
                            s = int(max(-1.0, min(1.0, v)) * 32767.0)
                            struct.pack_into("<h", pcm, i * 2, s)
                        pcm_parts.append(bytes(pcm))
                finally:
                    self._lib.qwen3_tts_free_result(res)
        return b"".join(pcm_parts), sr, time.time() - t0
