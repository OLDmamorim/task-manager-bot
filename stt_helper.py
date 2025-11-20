"""
Módulo para transcrição de áudio em texto (Speech-to-Text)
Usa OpenAI Whisper API
"""
import os
import logging
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)

# Cliente OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Diretório para arquivos temporários de áudio
AUDIO_DIR = Path("/tmp/stt_audio")
AUDIO_DIR.mkdir(exist_ok=True)


def transcribe_audio(audio_file_path: str, language: str = "pt") -> str:
    """
    Transcreve áudio em texto usando OpenAI Whisper
    
    Args:
        audio_file_path: Caminho do arquivo de áudio
        language: Código do idioma (padrão: "pt" para português)
    
    Returns:
        Texto transcrito ou None se houver erro
    """
    try:
        logger.info(f"🎤 Transcrevendo áudio: {audio_file_path}")
        
        # Abrir arquivo de áudio
        with open(audio_file_path, 'rb') as audio_file:
            # Chamar API Whisper da OpenAI
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="text"
            )
        
        # O resultado já é uma string com o texto transcrito
        transcribed_text = transcript.strip()
        
        logger.info(f"✅ Áudio transcrito com sucesso: '{transcribed_text[:50]}...'")
        return transcribed_text
        
    except Exception as e:
        logger.error(f"❌ Erro ao transcrever áudio: {e}", exc_info=True)
        return None


def download_telegram_voice(file_path: str, destination: str = None) -> str:
    """
    Copia arquivo de voz do Telegram para diretório de trabalho
    
    Args:
        file_path: Caminho do arquivo baixado pelo Telegram
        destination: Caminho de destino (opcional)
    
    Returns:
        Caminho do arquivo copiado
    """
    try:
        import shutil
        import time
        
        # Gerar nome de destino se não fornecido
        if not destination:
            timestamp = int(time.time())
            destination = AUDIO_DIR / f"voice_{timestamp}.ogg"
        
        # Copiar arquivo
        shutil.copy2(file_path, destination)
        
        logger.info(f"📥 Arquivo de voz copiado: {destination}")
        return str(destination)
        
    except Exception as e:
        logger.error(f"❌ Erro ao copiar arquivo de voz: {e}")
        return None


def cleanup_old_audio_files(max_age_hours: int = 1):
    """
    Remove arquivos de áudio antigos para economizar espaço
    
    Args:
        max_age_hours: Idade máxima em horas (padrão: 1 hora)
    """
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for audio_file in AUDIO_DIR.glob("*"):
            if audio_file.is_file():
                file_age = current_time - audio_file.stat().st_mtime
                if file_age > max_age_seconds:
                    audio_file.unlink()
                    logger.debug(f"🗑️ Arquivo de áudio antigo removido: {audio_file.name}")
                
    except Exception as e:
        logger.error(f"❌ Erro ao limpar arquivos de áudio: {e}")


# Limpar arquivos antigos ao importar o módulo
cleanup_old_audio_files()
