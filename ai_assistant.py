"""
AI Assistant - Assistente IA para Otimização de Tarefas
"""
import os
import json
import logging
from datetime import datetime
from openai import OpenAI
from tts_helper import text_to_speech

logger = logging.getLogger(__name__)

# Inicializar cliente OpenAI
client = OpenAI()


def get_ai_suggestion(tasks):
    """
    Obter sugestão do assistente IA baseada nas tarefas do utilizador
    
    Args:
        tasks: Lista de dicionários com as tarefas do utilizador
        
    Returns:
        dict: Sugestão estruturada com texto e ações
        {
            "tipo": "divisao_tarefa" | "prioridade" | "definir_data" | "agrupamento" | "sem_sugestao",
            "sugestao": "Texto da sugestão",
            "audio_path": "Caminho do arquivo de áudio (opcional)",
            "tarefa_id": int (opcional),
            "acoes": [
                {"texto": "Texto do botão", "callback": "callback_data"}
            ]
        }
    """
    
    if not tasks:
        return {
            "tipo": "sem_sugestao",
            "sugestao": "📭 Não tens tarefas pendentes. Aproveita para descansar! 😊",
            "acoes": []
        }
    
    # Preparar contexto das tarefas em formato JSON
    tasks_context = json.dumps(tasks, ensure_ascii=False, indent=2)
    
    # Criar prompt para o modelo de IA
    prompt = f"""Você é um assistente de produtividade de classe mundial. A sua tarefa é analisar a lista de tarefas de um utilizador português e fornecer UMA sugestão útil, concreta e acionável.

**Contexto (Lista de Tarefas do Utilizador):**
{tasks_context}

**Data de Hoje:** {datetime.now().strftime('%Y-%m-%d')}

**Regras:**
1. **Seja proativo:** Não espere por perguntas. Encontre oportunidades de melhoria.
2. **Foque-se em 1 sugestão de cada vez:** Escolha a mais impactante.
3. **Tipos de sugestões permitidas:**
   - **prioridade:** Se várias tarefas têm a mesma data, sugira qual deve ser a mais prioritária e porquê.
   - **divisao_tarefa:** Se uma tarefa parece muito grande ou vaga (ex: "Organizar evento"), sugira dividi-la em sub-tarefas específicas.
   - **definir_data:** Se uma tarefa importante não tem data, sugira definir uma com base na urgência.
   - **agrupamento:** Se há várias tarefas da mesma categoria/local, sugira focar-se nelas num dia específico.
4. **Tom:** Amigável, útil, mas não intrusivo. Use emojis apropriados. Escreva em português de Portugal.
5. **Formato da Resposta:** Responda APENAS em JSON válido, sem texto adicional antes ou depois.

**Exemplo de Resposta Esperada:**
{{
  "tipo": "divisao_tarefa",
  "sugestao": "💡 Vejo que a tarefa 'Organizar festa de Natal da empresa' é complexa. Quer dividi-la em sub-tarefas como 'Definir orçamento', 'Reservar local' e 'Enviar convites' para ser mais fácil de gerir?",
  "tarefa_id": 4,
  "acoes": [
    {{"texto": "✅ Sim, dividir tarefa", "callback": "ai_split_4"}},
    {{"texto": "❌ Não, obrigado", "callback": "ai_ignore"}}
  ]
}}

**Outro Exemplo:**
{{
  "tipo": "prioridade",
  "sugestao": "⚠️ Tens 3 tarefas para hoje. Sugiro focar primeiro em 'Comprar bilhetes de avião' pois é de prioridade alta e pode ter prazos externos.",
  "tarefa_id": 2,
  "acoes": [
    {{"texto": "✅ Concordo", "callback": "ai_accept"}},
    {{"texto": "❌ Prefiro outra", "callback": "ai_ignore"}}
  ]
}}

Se não houver nenhuma sugestão relevante, responda:
{{
  "tipo": "sem_sugestao",
  "sugestao": "🎯 As suas tarefas estão bem organizadas! Continue assim!",
  "acoes": []
}}

Responda agora em JSON:"""

    try:
        # Chamar API da OpenAI
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente de produtividade especializado em gestão de tarefas. Responda sempre em português de Portugal."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Extrair resposta
        suggestion_json = response.choices[0].message.content.strip()
        
        # Remover possíveis markdown code blocks
        if suggestion_json.startswith("```json"):
            suggestion_json = suggestion_json.replace("```json", "").replace("```", "").strip()
        elif suggestion_json.startswith("```"):
            suggestion_json = suggestion_json.replace("```", "").strip()
        
        # Parsear JSON
        suggestion = json.loads(suggestion_json)
        
        logger.info(f"✅ Sugestão IA obtida: {suggestion['tipo']}")
        
        # Gerar áudio da sugestão
        try:
            suggestion_text = suggestion.get('sugestao', '')
            if suggestion_text:
                audio_path = text_to_speech(suggestion_text)
                if audio_path:
                    suggestion['audio_path'] = audio_path
                    logger.info(f"🔊 Áudio gerado para sugestão")
        except Exception as audio_error:
            logger.warning(f"⚠️ Erro ao gerar áudio (continuando sem áudio): {audio_error}")
        
        return suggestion
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao parsear JSON da IA: {e}")
        logger.error(f"Resposta recebida: {suggestion_json}")
        return {
            "tipo": "erro",
            "sugestao": "🤖 Desculpe, tive dificuldade em analisar as suas tarefas. Tente novamente mais tarde.",
            "acoes": []
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter sugestão da IA: {e}", exc_info=True)
        return {
            "tipo": "erro",
            "sugestao": "🤖 Desculpe, não consegui analisar as suas tarefas neste momento.",
            "acoes": []
        }


def format_tasks_for_ai(tasks_from_db):
    """
    Formatar tarefas da base de dados para o formato esperado pela IA
    
    Args:
        tasks_from_db: Lista de tarefas da base de dados
        
    Returns:
        list: Lista de tarefas formatadas para a IA
    """
    formatted_tasks = []
    
    for task in tasks_from_db:
        formatted_tasks.append({
            "id": task['id'],
            "titulo": task['title'],
            "data": task.get('due_date'),
            "prioridade": task.get('priority', 'Média'),
            "categoria": task.get('category', 'Sem categoria')
        })
    
    return formatted_tasks
