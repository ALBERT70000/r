"""
Skill de Voz para R CLI.

Transcripción de audio con Whisper y síntesis de voz con Piper TTS.
Todo 100% local y offline.

Requisitos:
- whisper o faster-whisper para transcripción
- piper-tts para síntesis de voz
- sounddevice/pyaudio para grabación en tiempo real
"""

import json
import shutil
import subprocess
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

from r_cli.core.agent import Skill
from r_cli.core.llm import Tool


class VoiceSkill(Skill):
    """Skill para transcripción y síntesis de voz offline."""

    name = "voice"
    description = "Transcribe audio con Whisper y genera voz con Piper TTS"

    # Modelos Whisper disponibles
    WHISPER_MODELS = {
        "tiny": "Más rápido, menor precisión (~1GB VRAM)",
        "base": "Balance velocidad/precisión (~1GB VRAM)",
        "small": "Buena precisión (~2GB VRAM)",
        "medium": "Alta precisión (~5GB VRAM)",
        "large": "Máxima precisión (~10GB VRAM)",
        "large-v3": "Última versión, mejor calidad (~10GB VRAM)",
    }

    # Voces Piper populares (se pueden descargar)
    PIPER_VOICES = {
        "en_US-amy-medium": "Amy - English US female",
        "en_US-ryan-medium": "Ryan - English US male",
        "en_GB-alan-medium": "Alan - English UK male",
        "es_ES-davefx-medium": "Dave - Spanish Spain male",
        "es_MX-ald-medium": "Ald - Spanish Mexico male",
        "de_DE-thorsten-medium": "Thorsten - German male",
        "fr_FR-upmc-medium": "UPMC - French",
        "it_IT-riccardo-x_low": "Riccardo - Italian male",
        "pt_BR-faber-medium": "Faber - Portuguese Brazil male",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._whisper_available = self._check_whisper()
        self._piper_available = self._check_piper()
        self._sounddevice_available = self._check_sounddevice()

    def _check_whisper(self) -> bool:
        """Verifica si Whisper está disponible."""
        try:
            import whisper

            return True
        except ImportError:
            try:
                from faster_whisper import WhisperModel

                return True
            except ImportError:
                return False

    def _check_piper(self) -> bool:
        """Verifica si Piper TTS está disponible."""
        return shutil.which("piper") is not None

    def _check_sounddevice(self) -> bool:
        """Verifica si sounddevice está disponible."""
        try:
            import sounddevice

            return True
        except ImportError:
            return False

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="transcribe_audio",
                description="Transcribe un archivo de audio a texto usando Whisper",
                parameters={
                    "type": "object",
                    "properties": {
                        "audio_path": {
                            "type": "string",
                            "description": "Ruta al archivo de audio (mp3, wav, m4a, etc.)",
                        },
                        "model": {
                            "type": "string",
                            "enum": list(self.WHISPER_MODELS.keys()),
                            "description": "Modelo Whisper a usar (default: base)",
                        },
                        "language": {
                            "type": "string",
                            "description": "Código de idioma (es, en, fr, etc.). Auto-detecta si no se especifica.",
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["text", "srt", "vtt", "json"],
                            "description": "Formato de salida (default: text)",
                        },
                    },
                    "required": ["audio_path"],
                },
                handler=self.transcribe_audio,
            ),
            Tool(
                name="text_to_speech",
                description="Convierte texto a audio usando Piper TTS",
                parameters={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Texto a convertir en voz",
                        },
                        "voice": {
                            "type": "string",
                            "description": "Voz a usar (ver list_voices para opciones)",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Ruta donde guardar el audio (opcional)",
                        },
                        "speed": {
                            "type": "number",
                            "description": "Velocidad de habla (0.5-2.0, default: 1.0)",
                        },
                    },
                    "required": ["text"],
                },
                handler=self.text_to_speech,
            ),
            Tool(
                name="record_audio",
                description="Graba audio desde el micrófono",
                parameters={
                    "type": "object",
                    "properties": {
                        "duration": {
                            "type": "number",
                            "description": "Duración en segundos",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Ruta donde guardar la grabación",
                        },
                    },
                    "required": ["duration"],
                },
                handler=self.record_audio,
            ),
            Tool(
                name="list_whisper_models",
                description="Lista los modelos Whisper disponibles",
                parameters={"type": "object", "properties": {}},
                handler=self.list_whisper_models,
            ),
            Tool(
                name="list_voices",
                description="Lista las voces Piper TTS disponibles",
                parameters={"type": "object", "properties": {}},
                handler=self.list_voices,
            ),
            Tool(
                name="voice_chat",
                description="Modo conversación por voz (graba, transcribe, responde)",
                parameters={
                    "type": "object",
                    "properties": {
                        "duration": {
                            "type": "number",
                            "description": "Duración de grabación en segundos",
                        },
                    },
                    "required": ["duration"],
                },
                handler=self.voice_chat,
            ),
        ]

    def transcribe_audio(
        self,
        audio_path: str,
        model: str = "base",
        language: Optional[str] = None,
        output_format: str = "text",
    ) -> str:
        """Transcribe audio usando Whisper."""
        if not self._whisper_available:
            return "Error: Whisper no instalado. Ejecuta: pip install openai-whisper"

        audio_file = Path(audio_path)
        if not audio_file.exists():
            return f"Error: Archivo no encontrado: {audio_path}"

        try:
            # Intentar con faster-whisper primero (más eficiente)
            try:
                from faster_whisper import WhisperModel

                whisper_model = WhisperModel(model, device="auto", compute_type="auto")
                segments, info = whisper_model.transcribe(
                    str(audio_file),
                    language=language,
                    beam_size=5,
                )

                detected_lang = info.language
                segments_list = list(segments)

                if output_format == "text":
                    text = " ".join([seg.text.strip() for seg in segments_list])
                    return f"Transcripción ({detected_lang}):\n\n{text}"

                elif output_format == "srt":
                    srt_content = self._to_srt(segments_list)
                    return f"Subtítulos SRT:\n\n{srt_content}"

                elif output_format == "vtt":
                    vtt_content = self._to_vtt(segments_list)
                    return f"Subtítulos VTT:\n\n{vtt_content}"

                elif output_format == "json":
                    json_content = self._to_json(segments_list, detected_lang)
                    return f"Transcripción JSON:\n\n{json_content}"

            except ImportError:
                # Fallback a openai-whisper
                import whisper

                whisper_model = whisper.load_model(model)
                result = whisper_model.transcribe(
                    str(audio_file),
                    language=language,
                )

                if output_format == "text":
                    return (
                        f"Transcripción ({result.get('language', 'unknown')}):\n\n{result['text']}"
                    )

                elif output_format == "srt":
                    srt_content = self._whisper_to_srt(result)
                    return f"Subtítulos SRT:\n\n{srt_content}"

                elif output_format == "vtt":
                    vtt_content = self._whisper_to_vtt(result)
                    return f"Subtítulos VTT:\n\n{vtt_content}"

                elif output_format == "json":
                    return (
                        f"Transcripción JSON:\n\n{json.dumps(result, indent=2, ensure_ascii=False)}"
                    )

        except Exception as e:
            return f"Error transcribiendo audio: {e}"

    def _to_srt(self, segments) -> str:
        """Convierte segmentos a formato SRT."""
        srt_lines = []
        for i, seg in enumerate(segments, 1):
            start = self._format_timestamp_srt(seg.start)
            end = self._format_timestamp_srt(seg.end)
            srt_lines.append(f"{i}")
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(seg.text.strip())
            srt_lines.append("")
        return "\n".join(srt_lines)

    def _to_vtt(self, segments) -> str:
        """Convierte segmentos a formato VTT."""
        vtt_lines = ["WEBVTT", ""]
        for seg in segments:
            start = self._format_timestamp_vtt(seg.start)
            end = self._format_timestamp_vtt(seg.end)
            vtt_lines.append(f"{start} --> {end}")
            vtt_lines.append(seg.text.strip())
            vtt_lines.append("")
        return "\n".join(vtt_lines)

    def _to_json(self, segments, language: str) -> str:
        """Convierte segmentos a JSON."""
        data = {
            "language": language,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip(),
                }
                for seg in segments
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _format_timestamp_srt(self, seconds: float) -> str:
        """Formatea timestamp para SRT (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _format_timestamp_vtt(self, seconds: float) -> str:
        """Formatea timestamp para VTT (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    def _whisper_to_srt(self, result: dict) -> str:
        """Convierte resultado de whisper a SRT."""
        srt_lines = []
        for i, seg in enumerate(result.get("segments", []), 1):
            start = self._format_timestamp_srt(seg["start"])
            end = self._format_timestamp_srt(seg["end"])
            srt_lines.append(f"{i}")
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(seg["text"].strip())
            srt_lines.append("")
        return "\n".join(srt_lines)

    def _whisper_to_vtt(self, result: dict) -> str:
        """Convierte resultado de whisper a VTT."""
        vtt_lines = ["WEBVTT", ""]
        for seg in result.get("segments", []):
            start = self._format_timestamp_vtt(seg["start"])
            end = self._format_timestamp_vtt(seg["end"])
            vtt_lines.append(f"{start} --> {end}")
            vtt_lines.append(seg["text"].strip())
            vtt_lines.append("")
        return "\n".join(vtt_lines)

    def text_to_speech(
        self,
        text: str,
        voice: str = "en_US-amy-medium",
        output_path: Optional[str] = None,
        speed: float = 1.0,
    ) -> str:
        """Convierte texto a voz usando Piper TTS."""
        if not self._piper_available:
            return self._tts_fallback(text, output_path)

        try:
            # Determinar ruta de salida
            if output_path:
                out_path = Path(output_path)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_path = Path(self.output_dir) / f"speech_{timestamp}.wav"

            out_path.parent.mkdir(parents=True, exist_ok=True)

            # Ejecutar Piper
            # Piper espera el texto por stdin
            cmd = [
                "piper",
                "--model",
                voice,
                "--output_file",
                str(out_path),
            ]

            if speed != 1.0:
                cmd.extend(["--length_scale", str(1.0 / speed)])

            result = subprocess.run(
                cmd,
                check=False,
                input=text,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                return f"Error en Piper TTS: {result.stderr}"

            return f"Audio generado: {out_path}"

        except subprocess.TimeoutExpired:
            return "Error: Timeout generando audio (>120s)"
        except Exception as e:
            return f"Error en TTS: {e}"

    def _tts_fallback(self, text: str, output_path: Optional[str] = None) -> str:
        """Fallback usando say (macOS) o espeak (Linux)."""
        try:
            # Determinar ruta de salida
            if output_path:
                out_path = Path(output_path)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_path = Path(self.output_dir) / f"speech_{timestamp}.aiff"

            out_path.parent.mkdir(parents=True, exist_ok=True)

            # Intentar say (macOS)
            if shutil.which("say"):
                subprocess.run(
                    ["say", "-o", str(out_path), text],
                    check=True,
                    timeout=60,
                )
                return f"Audio generado (say): {out_path}"

            # Intentar espeak (Linux)
            elif shutil.which("espeak"):
                wav_path = out_path.with_suffix(".wav")
                subprocess.run(
                    ["espeak", "-w", str(wav_path), text],
                    check=True,
                    timeout=60,
                )
                return f"Audio generado (espeak): {wav_path}"

            else:
                return "Error: No hay TTS disponible. Instala piper-tts, o usa say (macOS) / espeak (Linux)"

        except Exception as e:
            return f"Error en TTS fallback: {e}"

    def record_audio(
        self,
        duration: float,
        output_path: Optional[str] = None,
    ) -> str:
        """Graba audio desde el micrófono."""
        if not self._sounddevice_available:
            return "Error: sounddevice no instalado. Ejecuta: pip install sounddevice"

        try:
            import numpy as np
            import sounddevice as sd

            # Parámetros de grabación
            sample_rate = 16000  # 16kHz es suficiente para voz
            channels = 1

            print(f"Grabando {duration} segundos...")

            # Grabar
            audio_data = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=channels,
                dtype=np.int16,
            )
            sd.wait()

            # Determinar ruta de salida
            if output_path:
                out_path = Path(output_path)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_path = Path(self.output_dir) / f"recording_{timestamp}.wav"

            out_path.parent.mkdir(parents=True, exist_ok=True)

            # Guardar como WAV
            with wave.open(str(out_path), "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())

            return f"Grabación guardada: {out_path}"

        except Exception as e:
            return f"Error grabando audio: {e}"

    def voice_chat(self, duration: float = 5.0) -> str:
        """Modo conversación: graba -> transcribe -> devuelve texto."""
        # Grabar audio
        record_result = self.record_audio(duration)
        if "Error" in record_result:
            return record_result

        # Extraer path de la grabación
        audio_path = record_result.split(": ")[-1]

        # Transcribir
        transcription = self.transcribe_audio(audio_path, model="base")

        # Limpiar archivo temporal si está en output_dir
        try:
            Path(audio_path).unlink()
        except Exception:
            pass

        return transcription

    def list_whisper_models(self) -> str:
        """Lista los modelos Whisper disponibles."""
        result = ["Modelos Whisper disponibles:\n"]

        for model, desc in self.WHISPER_MODELS.items():
            result.append(f"  - {model}: {desc}")

        result.append("\nUso: transcribe_audio(audio_path, model='medium')")
        result.append("\nInstalación: pip install openai-whisper")
        result.append("O para más velocidad: pip install faster-whisper")

        return "\n".join(result)

    def list_voices(self) -> str:
        """Lista las voces Piper TTS disponibles."""
        result = ["Voces Piper TTS disponibles:\n"]

        for voice, desc in self.PIPER_VOICES.items():
            result.append(f"  - {voice}: {desc}")

        result.append("\nUso: text_to_speech(text, voice='es_ES-davefx-medium')")
        result.append("\nDescargar voces: https://github.com/rhasspy/piper/releases")

        if not self._piper_available:
            result.append(
                "\n⚠️  Piper no instalado. Se usará say (macOS) / espeak (Linux) como fallback."
            )

        return "\n".join(result)

    def execute(self, **kwargs) -> str:
        """Ejecución directa del skill."""
        audio_path = kwargs.get("audio")
        text = kwargs.get("text")
        record_duration = kwargs.get("record")

        if audio_path:
            return self.transcribe_audio(
                audio_path=audio_path,
                model=kwargs.get("model", "base"),
                language=kwargs.get("language"),
                output_format=kwargs.get("format", "text"),
            )
        elif text:
            return self.text_to_speech(
                text=text,
                voice=kwargs.get("voice", "en_US-amy-medium"),
                output_path=kwargs.get("output"),
                speed=kwargs.get("speed", 1.0),
            )
        elif record_duration:
            return self.record_audio(
                duration=float(record_duration),
                output_path=kwargs.get("output"),
            )
        else:
            return "Error: Especifica --audio para transcribir, --text para TTS, o --record para grabar"
