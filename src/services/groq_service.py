"""Groq AI service for TTS and STT functionality."""

import io
import logging
from typing import Optional, BinaryIO
from pathlib import Path

from groq import Groq
from groq.types.audio import Transcription
from fastapi import HTTPException

from src.core.config import settings

logger = logging.getLogger(__name__)


class GroqService:
    """Service for interacting with Groq AI APIs (TTS and STT)."""

    def __init__(self):
        """Initialize Groq service."""
        if not settings.groq_api_key:
            logger.warning("GROQ_API_KEY not configured. Voice features will be disabled.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=settings.groq_api_key)
                logger.info("Groq client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None

        # Available TTS voices
        self.tts_voices_english = [
            "Arista-PlayAI", "Atlas-PlayAI", "Basil-PlayAI", "Briggs-PlayAI",
            "Calum-PlayAI", "Celeste-PlayAI", "Cheyenne-PlayAI", "Chip-PlayAI",
            "Cillian-PlayAI", "Deedee-PlayAI", "Fritz-PlayAI", "Gail-PlayAI",
            "Indigo-PlayAI", "Mamaw-PlayAI", "Mason-PlayAI", "Mikail-PlayAI",
            "Mitch-PlayAI", "Quinn-PlayAI", "Thunder-PlayAI"
        ]

        self.tts_voices_arabic = [
            "Ahmad-PlayAI", "Amira-PlayAI", "Khalid-PlayAI", "Nasser-PlayAI"
        ]

    def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        model: str = "playai-tts",
        response_format: str = "wav"
    ) -> bytes:
        """
        Convert text to speech using Groq PlayAI TTS.

        Args:
            text: Text to convert to speech (max 10K characters)
            voice: Voice to use (defaults to Fritz-PlayAI)
            model: TTS model to use (playai-tts or playai-tts-arabic)
            response_format: Audio format (currently only "wav" supported)

        Returns:
            Audio data as bytes

        Raises:
            HTTPException: If TTS fails or Groq is not configured
        """
        if not self.client:
            raise HTTPException(
                status_code=503,
                detail="Voice features are not available. Please configure GROQ_API_KEY."
            )

        # Default voice based on model
        if not voice:
            voice = "Fritz-PlayAI" if model == "playai-tts" else "Ahmad-PlayAI"

        # Validate voice for model
        if model == "playai-tts" and voice not in self.tts_voices_english:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid voice for English model. Choose from: {', '.join(self.tts_voices_english)}"
            )
        elif model == "playai-tts-arabic" and voice not in self.tts_voices_arabic:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid voice for Arabic model. Choose from: {', '.join(self.tts_voices_arabic)}"
            )

        # Validate text length
        if len(text) > 10000:
            raise HTTPException(
                status_code=400,
                detail="Text exceeds maximum length of 10,000 characters"
            )

        try:
            logger.info(f"Generating TTS for {len(text)} characters with voice {voice}")

            # Call Groq TTS API
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=response_format
            )

            # Get audio bytes
            audio_bytes = response.read()

            logger.info(f"TTS generation successful, {len(audio_bytes)} bytes generated")
            return audio_bytes

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate speech: {str(e)}"
            )

    def speech_to_text(
        self,
        audio_file: BinaryIO,
        filename: str,
        model: str = "whisper-large-v3-turbo",
        language: Optional[str] = "en",
        prompt: Optional[str] = None,
        response_format: str = "json",
        temperature: float = 0.0
    ) -> dict:
        """
        Transcribe audio to text using Groq Whisper.

        Args:
            audio_file: Audio file binary data
            filename: Original filename (for format detection)
            model: Whisper model to use
            language: Language code (ISO-639-1)
            prompt: Optional prompt to guide style
            response_format: Response format (json, verbose_json, or text)
            temperature: Sampling temperature (0-1)

        Returns:
            Transcription result as dictionary

        Raises:
            HTTPException: If STT fails or Groq is not configured
        """
        if not self.client:
            raise HTTPException(
                status_code=503,
                detail="Voice features are not available. Please configure GROQ_API_KEY."
            )

        # Validate file format
        allowed_formats = ['.flac', '.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.ogg', '.wav', '.webm']
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Supported formats: {', '.join(allowed_formats)}"
            )

        try:
            logger.info(f"Transcribing audio file: {filename} with model {model}")

            # Prepare transcription parameters
            transcription_params = {
                "file": (filename, audio_file, f"audio/{file_ext[1:]}"),
                "model": model,
                "response_format": response_format,
                "temperature": temperature
            }

            # Add optional parameters
            if language:
                transcription_params["language"] = language
            if prompt:
                transcription_params["prompt"] = prompt[:224]  # Max 224 tokens

            # Call Groq Whisper API
            transcription: Transcription = self.client.audio.transcriptions.create(
                **transcription_params
            )

            # Convert response to dictionary based on format
            if response_format == "text":
                result = {"text": transcription}
            elif response_format in ["json", "verbose_json"]:
                result = transcription.model_dump() if hasattr(transcription, 'model_dump') else {
                    "text": transcription.text,
                    "language": getattr(transcription, 'language', language),
                    "duration": getattr(transcription, 'duration', None),
                }

                # Add verbose metadata if available
                if response_format == "verbose_json" and hasattr(transcription, 'segments'):
                    result["segments"] = transcription.segments
                    result["words"] = getattr(transcription, 'words', [])
            else:
                result = {"text": str(transcription)}

            logger.info(f"Transcription successful: {len(result.get('text', ''))} characters")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to transcribe audio: {str(e)}"
            )

    def translate_speech(
        self,
        audio_file: BinaryIO,
        filename: str,
        model: str = "whisper-large-v3",
        prompt: Optional[str] = None,
        response_format: str = "json",
        temperature: float = 0.0
    ) -> dict:
        """
        Translate audio to English text using Groq Whisper.

        Args:
            audio_file: Audio file binary data
            filename: Original filename (for format detection)
            model: Whisper model to use
            prompt: Optional prompt to guide style
            response_format: Response format (json, verbose_json, or text)
            temperature: Sampling temperature (0-1)

        Returns:
            Translation result as dictionary

        Raises:
            HTTPException: If translation fails or Groq is not configured
        """
        if not self.client:
            raise HTTPException(
                status_code=503,
                detail="Voice features are not available. Please configure GROQ_API_KEY."
            )

        # Validate file format
        allowed_formats = ['.flac', '.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.ogg', '.wav', '.webm']
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Supported formats: {', '.join(allowed_formats)}"
            )

        try:
            logger.info(f"Translating audio file: {filename} with model {model}")

            # Prepare translation parameters
            translation_params = {
                "file": (filename, audio_file, f"audio/{file_ext[1:]}"),
                "model": model,
                "response_format": response_format,
                "temperature": temperature
            }

            # Add optional parameters
            if prompt:
                translation_params["prompt"] = prompt[:224]  # Max 224 tokens

            # Call Groq Whisper API for translation
            translation = self.client.audio.translations.create(
                **translation_params
            )

            # Convert response to dictionary
            if response_format == "text":
                result = {"text": translation}
            else:
                result = translation.model_dump() if hasattr(translation, 'model_dump') else {
                    "text": translation.text,
                    "language": "en",  # Translations are always to English
                }

            logger.info(f"Translation successful: {len(result.get('text', ''))} characters")
            return result

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to translate audio: {str(e)}"
            )

    def is_available(self) -> bool:
        """Check if Groq service is available."""
        return self.client is not None

    def get_available_voices(self, language: str = "english") -> list[str]:
        """
        Get list of available voices for a language.

        Args:
            language: Language ("english" or "arabic")

        Returns:
            List of available voice names
        """
        if language.lower() == "arabic":
            return self.tts_voices_arabic
        return self.tts_voices_english


# Global service instance
groq_service = GroqService()