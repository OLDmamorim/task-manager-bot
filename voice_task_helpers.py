"""
Funções auxiliares para criação de tarefas por voz
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from tasks import get_user_categories, create_task
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def ask_category_for_voice_task(query, context):
    """Perguntar categoria ao utilizador"""
    user_id = context.user_data.get('user_id')
    
    # Obter categorias do utilizador
    categories = get_user_categories(user_id)
    
    keyboard = []
    
    # Adicionar categorias existentes
    if categories:
        for cat in categories[:10]:  # Limitar a 10 categorias
            keyboard.append([InlineKeyboardButton(
                f"{cat['emoji']} {cat['name']}", 
                callback_data=f"category_{cat['name']}"
            )])
    
    # Opção sem categoria
    keyboard.append([InlineKeyboardButton("📭 Sem categoria", callback_data="category_none")])
    
    await query.message.reply_text(
        "🏷️ <b>Escolha a categoria:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def create_voice_task_final(query, context, add_to_gcal=False):
    """Criar tarefa final com todos os dados recolhidos"""
    try:
        user_id = context.user_data.get('user_id')
        task_data = context.user_data.get('task_data', {})
        
        # Preparar dados da tarefa
        title = task_data.get('title')
        due_date = task_data.get('due_date')
        due_time = task_data.get('due_time')
        priority = task_data.get('priority', 'Média')
        category = task_data.get('category')
        
        # Combinar data e hora se ambos existirem
        if due_date and due_time:
            due_date = f"{due_date} {due_time}"
        
        # Criar tarefa
        task_id = create_task(
            user_id=user_id,
            title=title,
            due_date=due_date,
            priority=priority,
            category=category
        )
        
        # Formatar mensagem de confirmação
        confirmation_text = f"✅ <b>Tarefa criada com sucesso!</b>\n\n"
        confirmation_text += f"📋 <b>Título:</b> {title}\n"
        
        if due_date:
            try:
                if ' ' in str(due_date):
                    date_obj = datetime.strptime(str(due_date), '%Y-%m-%d %H:%M')
                    confirmation_text += f"📅 <b>Data:</b> {date_obj.strftime('%d/%m/%Y às %H:%M')}\n"
                else:
                    date_obj = datetime.strptime(str(due_date), '%Y-%m-%d')
                    confirmation_text += f"📅 <b>Data:</b> {date_obj.strftime('%d/%m/%Y')}\n"
            except:
                confirmation_text += f"📅 <b>Data:</b> {due_date}\n"
        
        priority_emoji = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}.get(priority, "🟡")
        confirmation_text += f"⚡ <b>Prioridade:</b> {priority_emoji} {priority}\n"
        
        if category:
            confirmation_text += f"🏷️ <b>Categoria:</b> {category}\n"
        
        # Google Calendar
        if add_to_gcal and due_date:
            try:
                from google_calendar import add_task_to_calendar
                event_id = add_task_to_calendar(user_id, task_id, title, due_date, category)
                
                if event_id:
                    confirmation_text += f"\n📆 <b>Adicionado ao Google Calendar!</b>"
                    logger.info(f"✅ Tarefa {task_id} adicionada ao Google Calendar: {event_id}")
                else:
                    confirmation_text += f"\n⚠️ Não foi possível adicionar ao Google Calendar"
            except Exception as e:
                logger.error(f"❌ Erro ao adicionar ao Google Calendar: {e}")
                confirmation_text += f"\n⚠️ Erro ao adicionar ao Google Calendar"
        
        await query.edit_message_text(confirmation_text, parse_mode='HTML')
        
        # Limpar dados temporários
        context.user_data.pop('creating_task', None)
        context.user_data.pop('task_data', None)
        
        logger.info(f"✅ Tarefa criada por voz: ID {task_id}, GCal: {add_to_gcal}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar tarefa por voz: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Desculpe, ocorreu um erro ao criar a tarefa. Por favor, tente novamente.",
            parse_mode='HTML'
        )
