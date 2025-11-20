"""
Módulo para conversão de texto em áudio (Text-to-Speech)
Usa OpenAI TTS API
"""
import os
import logging
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)

# Cliente OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Diretório para arquivos temporários de áudio
AUDIO_DIR = Path("/tmp/tts_audio")
AUDIO_DIR.mkdir(exist_ok=True)

def text_to_speech(text: str, filename: str = None) -> str:
    """
    Converte texto em áudio usando OpenAI TTS
    
    Args:
        text: Texto para converter
        filename: Nome do arquivo (opcional, gera automaticamente se não fornecido)
    
    Returns:
        Caminho completo do arquivo de áudio gerado
    """
    try:
        # Gerar nome de arquivo se não fornecido
        if not filename:
            import time
            filename = f"tts_{int(time.time())}.mp3"
        
        # Caminho completo
        audio_path = AUDIO_DIR / filename
        
        logger.info(f"🔊 Gerando áudio TTS: {filename}")
        
        # Chamar API da OpenAI TTS
        response = client.audio.speech.create(
            model="tts-1",  # Modelo rápido e econômico
            voice="nova",   # Voz feminina natural (outras opções: alloy, echo, fable, onyx, shimmer)
            input=text,
            speed=1.0       # Velocidade normal
        )
        
        # Salvar áudio
        response.stream_to_file(str(audio_path))
        
        logger.info(f"✅ Áudio gerado com sucesso: {audio_path}")
        return str(audio_path)
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar áudio TTS: {e}")
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
        
        for audio_file in AUDIO_DIR.glob("*.mp3"):
            file_age = current_time - audio_file.stat().st_mtime
            if file_age > max_age_seconds:
                audio_file.unlink()
                logger.debug(f"🗑️ Arquivo de áudio antigo removido: {audio_file.name}")
                
    except Exception as e:
        logger.error(f"❌ Erro ao limpar arquivos de áudio: {e}")

# Limpar arquivos antigos ao importar o módulo
cleanup_old_audio_files()
