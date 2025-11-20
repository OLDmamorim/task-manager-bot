"""
Módulo para análise inteligente de comandos de voz para criação de tarefas
Usa IA para extrair informações estruturadas do texto transcrito
"""
import os
import json
import logging
from datetime import datetime, timedelta
from openai import OpenAI

logger = logging.getLogger(__name__)

# Cliente OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def parse_voice_task(transcribed_text: str) -> dict:
    """
    Analisa texto transcrito e extrai informações da tarefa
    
    Args:
        transcribed_text: Texto transcrito da mensagem de voz
    
    Returns:
        dict: Informações extraídas da tarefa
        {
            "title": str,
            "due_date": str (YYYY-MM-DD) ou None,
            "due_time": str (HH:MM) ou None,
            "priority": "Alta" | "Média" | "Baixa" ou None,
            "category": str ou None,
            "confidence": float (0-1),
            "missing_fields": list[str]
        }
    """
    try:
        logger.info(f"🧠 Analisando comando de voz: '{transcribed_text}'")
        
        # Data atual para contexto
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        weekday_pt = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", 
                      "sexta-feira", "sábado", "domingo"][today.weekday()]
        
        # Criar prompt para IA
        prompt = f"""Você é um assistente especializado em extrair informações de tarefas a partir de comandos de voz em português.

**Data e Hora Atual:**
- Data: {today_str} ({weekday_pt})
- Hora: {today.strftime("%H:%M")}

**Comando de Voz do Utilizador:**
"{transcribed_text}"

**Sua Tarefa:**
Extraia as seguintes informações da tarefa mencionada pelo utilizador:

1. **Título** (obrigatório): O que o utilizador quer fazer
2. **Data** (opcional): Quando fazer (formato YYYY-MM-DD)
   - "hoje" = {today_str}
   - "amanhã" = {(today + timedelta(days=1)).strftime("%Y-%m-%d")}
   - "segunda", "terça", etc. = próxima ocorrência desse dia
   - Datas específicas como "25 de novembro", "dia 15", etc.
3. **Hora** (opcional): A que horas (formato HH:MM em 24h)
   - "15h", "às três da tarde" = 15:00
   - "meio-dia" = 12:00
   - "meia-noite" = 00:00
4. **Prioridade** (opcional): Alta, Média ou Baixa
   - Palavras como "urgente", "importante", "crítico" = Alta
   - Palavras como "quando puder", "não urgente" = Baixa
   - Padrão se não mencionado = Média
5. **Categoria** (opcional): Tipo de tarefa (trabalho, pessoal, compras, etc.)

**Formato de Resposta (JSON):**
{{
  "title": "Título da tarefa",
  "due_date": "YYYY-MM-DD" ou null,
  "due_time": "HH:MM" ou null,
  "priority": "Alta" | "Média" | "Baixa" ou null,
  "category": "nome da categoria" ou null,
  "confidence": 0.0-1.0,
  "missing_fields": ["lista", "de", "campos", "em", "falta"]
}}

**Regras:**
- Se algo não for mencionado, use null
- confidence = quão confiante está na extração (0.0 a 1.0)
- missing_fields = campos que seria bom perguntar ao utilizador
- Seja inteligente com datas relativas (hoje, amanhã, próxima segunda, etc.)
- Normalize prioridades para exatamente: "Alta", "Média" ou "Baixa"

Responda APENAS com o JSON, sem explicações adicionais."""

        # Chamar IA
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em análise de comandos de voz para gestão de tarefas. Responda sempre em JSON válido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # Extrair resposta
        result_json = response.choices[0].message.content.strip()
        
        # Remover possíveis markdown code blocks
        if result_json.startswith("```json"):
            result_json = result_json.replace("```json", "").replace("```", "").strip()
        elif result_json.startswith("```"):
            result_json = result_json.replace("```", "").strip()
        
        # Parsear JSON
        parsed_task = json.loads(result_json)
        
        logger.info(f"✅ Tarefa analisada: {parsed_task['title']} (confiança: {parsed_task.get('confidence', 0):.2f})")
        
        return parsed_task
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao parsear JSON da IA: {e}")
        logger.error(f"Resposta recebida: {result_json}")
        return {
            "title": transcribed_text,  # Fallback: usar texto completo como título
            "due_date": None,
            "due_time": None,
            "priority": None,
            "category": None,
            "confidence": 0.3,
            "missing_fields": ["due_date", "priority", "category"]
        }
    except Exception as e:
        logger.error(f"❌ Erro ao analisar comando de voz: {e}", exc_info=True)
        return {
            "title": transcribed_text,
            "due_date": None,
            "due_time": None,
            "priority": None,
            "category": None,
            "confidence": 0.0,
            "missing_fields": ["due_date", "priority", "category"]
        }


def should_ask_for_details(parsed_task: dict) -> bool:
    """
    Determina se deve perguntar detalhes ao utilizador ou criar tarefa diretamente
    
    Args:
        parsed_task: Tarefa parseada pela IA
    
    Returns:
        bool: True se deve perguntar, False se pode criar diretamente
    """
    # SEMPRE perguntar detalhes para permitir escolha de hora e Google Calendar
    return True
