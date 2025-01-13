# MAJOR/FIR/accounts/speech_processor.py
import speech_recognition as sr
import logging
from pydub import AudioSegment
import os
from django.conf import settings

logger=logging.getLogger(__name__)
class SpeechProcessor:
    @staticmethod
    def convert_webm_to_wav(webm_path):
        """Convert WebM audio to WAV format for speech recognition"""
        print(f"Converting {webm_path} to WAV")
        try:
            full_webm_path = os.path.join(settings.MEDIA_ROOT, webm_path)
            wav_path = full_webm_path.replace('.webm', '.wav')            
            print(f"Full webm path: {full_webm_path}")
            print(f"WAV path: {wav_path}")    
            # Convert WebM to WAV
            audio = AudioSegment.from_file(full_webm_path)
            audio.export(wav_path, format="wav")
            print("WAV conversion successful")          
            return wav_path
        except Exception as e:
            print(f"Error in convert_webm_to_wav: {str(e)}")
            raise   
    @staticmethod
    def extract_text(audio_path):
        logger.info(f"Starting text extraction from {audio_path}")
        print(f"Received audio_path: {audio_path}")
        print(f"File exists check: {os.path.exists(os.path.join(settings.MEDIA_ROOT, audio_path))}")
        try:
            if audio_path.endswith('.webm'):
                logger.info("Converting webm to wav")
                audio_path = SpeechProcessor.convert_webm_to_wav(audio_path)
                logger.info(f"Converted to WAV: {audio_path}")
                
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                logger.info("Reading audio file")
                audio_data = recognizer.record(source)
                logger.info("Audio file read successfully")
                
                try:
                    logger.info("Starting Google Speech Recognition")
                    text = recognizer.recognize_google(audio_data, language='en-IN')
                    logger.info(f"Extracted text: {text}")
                    return text
                except sr.UnknownValueError as e:
                    logger.error(f"Speech recognition error: {str(e)}")
                    return "Speech recognition could not understand the audio"
                except sr.RequestError as e:
                    logger.error(f"Google API error: {str(e)}")
                    return "Could not access the speech recognition service"
        except Exception as e:
            logger.error(f"Error in extract_text: {str(e)}")
            return f"Error processing audio: {str(e)}"