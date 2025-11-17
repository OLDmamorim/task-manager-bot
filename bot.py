"""
Task Manager Bot - Bot de Gestão de Tarefas (Versão Corrigida)
"""
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import get_db, init_db, register_user, add_default_categories
from tasks import (
    create_task, get_user_tasks, get_task_by_id, complete_task,
    delete_task, get_stats
)
from calendar_utils import get_month_calendar, handle_calendar_callback

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')


# ==================== FUNÇÕES AUXILIARES ====================

def get_priority_emoji(priority):
    """Obter emoji para prioridade"""
    emojis = {'Alta': '🔴', 'Média': '🟡', 'Baixa': '🟢'}
    return emojis.get(priority, '⚪')


def format_task_text(task):
    """Formatar texto de uma tarefa"""
    priority = get_priority_emoji(task['priority'])
    title = task['title']
    
    text = f"{priority} <b>{title}</b>\n"
    
    if task['due_date']:
        try:
            date_obj = datetime.strptime(task['due_date'], '%Y-%m-%d')
            today = datetime.now().date()
            task_date = date_obj.date()
            
            if task_date == today:
                date_text = "Hoje"
            elif task_date == today + timedelta(days=1):
                date_text = "Amanhã"
            elif task_date < today:
                days = (today - task_date).days
                date_text = f"Há {days} dia(s)"
            else:
                days = (task_date - today).days
                date_text = f"Em {days} dia(s)"
            
            text += f"   📅 {date_text}\n"
        except:
            pass
    
    text += f"   ID: <code>{task['id']}</code>\n"
    return text


# ==================== COMANDOS BÁSICOS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user = update.effective_user
    register_user(user.id, user.username, user.first_name, user.last_name)
    add_default_categories(user.id)
    
    text = f"""
👋 <b>Olá, {user.first_name}!</b>

Bem-vindo ao <b>Task Manager Bot</b>!

📋 <b>Comandos principais:</b>
/nova_tarefa - Criar tarefa
/tarefas_ativas - Ver tarefas com checkboxes
/tarefas - Ver todas as tarefas
/hoje - Tarefas de hoje
/concluir - Marcar como concluída
/apagar_tarefa - Apagar tarefa
/stats - Estatísticas

Digite /help para ver todos os comandos!
"""
    await update.message.reply_text(text, parse_mode='HTML')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    text = """
📚 <b>Comandos Disponíveis:</b>

<b>Tarefas:</b>
/nova_tarefa - Criar nova tarefa
/tarefas_ativas - Ver tarefas pendentes (com checkboxes)
/tarefas - Ver todas as tarefas
/hoje - Tarefas para hoje
/concluir - Marcar como concluída
/apagar_tarefa - Apagar tarefa

<b>Estatísticas:</b>
/stats - Ver estatísticas

<b>Ajuda:</b>
/help - Mostrar esta mensagem
"""
    await update.message.reply_text(text, parse_mode='HTML')


# ==================== CRIAR TAREFA ====================

async def nova_tarefa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /nova_tarefa"""
    context.user_data['creating_task'] = True
    context.user_data['task_data'] = {}
    context.user_data['user_id'] = update.effective_user.id
    
    text = "📝 <b>Criar Nova Tarefa</b>\n\nEnvie o <b>título</b> da tarefa:"
    await update.message.reply_text(text, parse_mode='HTML')


# ==================== LISTAR TAREFAS ====================

async def tarefas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /tarefas - Listar todas as tarefas"""
    user_id = update.effective_user.id
    tasks = get_user_tasks(user_id, completed=False)
    
    if not tasks:
        await update.message.reply_text("📭 Não tens tarefas pendentes!")
        return
    
    text = "📋 <b>Tarefas Pendentes:</b>\n\n"
    
    for task in tasks:
        text += format_task_text(task) + "\n"
    
    await update.message.reply_text(text, parse_mode='HTML')


async def tarefas_ativas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /tarefas_ativas - Listar tarefas pendentes com checkboxes"""
    user_id = update.effective_user.id
    tasks = get_user_tasks(user_id, completed=False)
    
    if not tasks:
        await update.message.reply_text("📭 Não tens tarefas pendentes!")
        return
    
    keyboard = []
    
    for task in tasks[:15]:
        priority = get_priority_emoji(task['priority'])
        title = task['title'][:40]
        
        button_text = f"☐ {priority} {title}"
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"check_{task['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Fechar", callback_data="cancel")])
    
    await update.message.reply_text(
        "✅ <b>Tarefas Ativas</b>\n\nClica para marcar como concluída:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def hoje_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /hoje - Tarefas de hoje"""
    user_id = update.effective_user.id
    tasks = get_user_tasks(user_id, completed=False)
    
    today = datetime.now().date()
    today_tasks = []
    
    for task in tasks:
        if task['due_date']:
            try:
                task_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                if task_date == today:
                    today_tasks.append(task)
            except:
                pass
    
    if not today_tasks:
        await update.message.reply_text("📅 Não tens tarefas para hoje!")
        return
    
    text = "📅 <b>Tarefas de Hoje:</b>\n\n"
    
    for task in today_tasks:
        text += format_task_text(task) + "\n"
    
    await update.message.reply_text(text, parse_mode='HTML')


# ==================== CONCLUIR TAREFA ====================

async def concluir_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /concluir"""
    user_id = update.effective_user.id
    tasks = get_user_tasks(user_id, completed=False)
    
    if not tasks:
        await update.message.reply_text("📭 Não tens tarefas pendentes!")
        return
    
    keyboard = []
    
    for task in tasks[:10]:
        keyboard.append([InlineKeyboardButton(
            f"✅ {task['title']}",
            callback_data=f"complete_{task['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
    
    await update.message.reply_text(
        "✅ <b>Concluir Tarefa</b>\n\nSelecione a tarefa:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ==================== APAGAR TAREFA ====================

async def apagar_tarefa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /apagar_tarefa"""
    user_id = update.effective_user.id
    tasks = get_user_tasks(user_id, completed=False)
    
    if not tasks:
        await update.message.reply_text("📭 Não tens tarefas pendentes!")
        return
    
    keyboard = []
    
    for task in tasks[:10]:
        keyboard.append([InlineKeyboardButton(
            f"🗑️ {task['title']}",
            callback_data=f"delete_{task['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
    
    await update.message.reply_text(
        "🗑️ <b>Apagar Tarefa</b>\n\nSelecione a tarefa:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


# ==================== ESTATÍSTICAS ====================

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stats"""
    user_id = update.effective_user.id
    stats = get_stats(user_id)
    
    text = f"""
📊 <b>Suas Estatísticas</b>

📋 Total de tarefas: <b>{stats['total']}</b>
✅ Concluídas: <b>{stats['completed']}</b>
⏳ Pendentes: <b>{stats['pending']}</b>
📈 Taxa de conclusão: <b>{stats['completion_rate']:.1f}%</b>

🎯 <b>Hoje:</b> {stats['completed_today']} concluída(s)
📅 <b>Esta semana:</b> {stats['completed_week']} concluída(s)
"""
    
    await update.message.reply_text(text, parse_mode='HTML')


# ==================== CALLBACK HANDLER ====================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para callbacks dos botões"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Cancelar
    if data == "cancel":
        await query.edit_message_text("❌ Operação cancelada.")
        return
    
    # Checkbox - Marcar como concluída
    if data.startswith("check_"):
        task_id = int(data.replace("check_", ""))
        task = get_task_by_id(task_id)
        
        if task:
            complete_task(task_id)
            await query.edit_message_text(
                f"✅ <b>Tarefa concluída!</b>\n\n📋 {task['title']}\n\n🎉 Parabéns!",
                parse_mode='HTML'
            )
        return
    
    # Concluir tarefa
    if data.startswith("complete_"):
        task_id = int(data.replace("complete_", ""))
        task = get_task_by_id(task_id)
        
        if task:
            complete_task(task_id)
            await query.edit_message_text(
                f"✅ <b>Tarefa concluída!</b>\n\n📋 {task['title']}\n\n🎉 Parabéns!",
                parse_mode='HTML'
            )
        return
    
    # Apagar tarefa
    if data.startswith("delete_"):
        task_id = int(data.replace("delete_", ""))
        task = get_task_by_id(task_id)
        
        if task:
            delete_task(task_id)
            await query.edit_message_text(
                f"🗑️ <b>Tarefa apagada!</b>\n\n📋 {task['title']}",
                parse_mode='HTML'
            )
        return
    
    # Prioridade
    if data.startswith("priority_"):
        priority = data.replace("priority_", "")
        context.user_data['task_data']['priority'] = priority
        
        # Mostrar calendário
        now = datetime.now()
        calendar = get_month_calendar(now.year, now.month)
        context.user_data['cal_year'] = now.year
        context.user_data['cal_month'] = now.month
        
        await query.edit_message_text(
            f"✅ Prioridade: <b>{priority}</b>\n\n📅 <b>Escolhe a data:</b>",
            reply_markup=calendar,
            parse_mode='HTML'
        )
        return
    
    # Calendário
    if data.startswith("cal_"):
        current_year = context.user_data.get('cal_year')
        current_month = context.user_data.get('cal_month')
        
        action, year, month, date = handle_calendar_callback(data, current_year, current_month)
        
        if action == "cancel":
            await query.edit_message_text("❌ Operação cancelada.")
            context.user_data.pop('creating_task', None)
            context.user_data.pop('task_data', None)
            return
        
        elif action == "ignore":
            return
        
        elif action in ["prev", "next"]:
            calendar = get_month_calendar(year, month)
            context.user_data['cal_year'] = year
            context.user_data['cal_month'] = month
            
            await query.edit_message_reply_markup(reply_markup=calendar)
            return
        
        elif action == "select":
            # Data selecionada - criar tarefa
            context.user_data['task_data']['due_date'] = date
            
            task_data = context.user_data['task_data']
            user_id = context.user_data.get('user_id')
            
            task_id = create_task(
                user_id=user_id,
                title=task_data['title'],
                priority=task_data['priority'],
                due_date=task_data['due_date']
            )
            
            date_formatted = datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
            
            await query.edit_message_text(
                f"✅ <b>Tarefa criada!</b>\n\n"
                f"📋 {task_data['title']}\n"
                f"⚡ Prioridade: {task_data['priority']}\n"
                f"📅 Data: {date_formatted}\n"
                f"ID: <code>{task_id}</code>",
                parse_mode='HTML'
            )
            
            # Limpar context
            context.user_data.pop('creating_task', None)
            context.user_data.pop('task_data', None)
            context.user_data.pop('cal_year', None)
            context.user_data.pop('cal_month', None)
            context.user_data.pop('user_id', None)
        return


# ==================== MESSAGE HANDLER ====================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens de texto"""
    text = update.message.text.strip()
    
    # Criar tarefa - Título
    if context.user_data.get('creating_task') and 'title' not in context.user_data.get('task_data', {}):
        context.user_data['task_data']['title'] = text
        
        # Pedir prioridade
        keyboard = [
            [InlineKeyboardButton("🔴 Alta", callback_data="priority_Alta")],
            [InlineKeyboardButton("🟡 Média", callback_data="priority_Média")],
            [InlineKeyboardButton("🟢 Baixa", callback_data="priority_Baixa")],
        ]
        
        await update.message.reply_text(
            "⚡ <b>Escolha a prioridade:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return


# ==================== ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler global para erros"""
    logger.error(f"Erro ao processar update: {context.error}")
    
    # Tentar notificar o utilizador
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Ocorreu um erro ao processar o seu pedido. Por favor, tente novamente."
            )
    except:
        pass


# ==================== MAIN ====================

async def setup_commands(app):
    """Configurar comandos do bot"""
    commands = [
        BotCommand("start", "Iniciar o bot"),
        BotCommand("help", "Mostrar ajuda"),
        BotCommand("nova_tarefa", "Criar nova tarefa"),
        BotCommand("tarefas_ativas", "Ver tarefas pendentes (com checkboxes)"),
        BotCommand("tarefas", "Ver todas as tarefas"),
        BotCommand("hoje", "Tarefas de hoje"),
        BotCommand("concluir", "Marcar como concluída"),
        BotCommand("apagar_tarefa", "Apagar tarefa"),
        BotCommand("stats", "Ver estatísticas"),
    ]
    await app.bot.set_my_commands(commands)


def main():
    """Iniciar bot"""
    # Inicializar BD
    init_db()
    
    # Criar aplicação
    app = Application.builder().token(TOKEN).build()
    
    # Registar comandos
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('nova_tarefa', nova_tarefa_command))
    app.add_handler(CommandHandler('tarefas_ativas', tarefas_ativas_command))
    app.add_handler(CommandHandler('tarefas', tarefas_command))
    app.add_handler(CommandHandler('hoje', hoje_command))
    app.add_handler(CommandHandler('concluir', concluir_command))
    app.add_handler(CommandHandler('apagar_tarefa', apagar_tarefa_command))
    app.add_handler(CommandHandler('stats', stats_command))
    
    # Handlers
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    # Configurar comandos
    app.post_init = setup_commands
    
    # Iniciar bot
    logger.info("🤖 Bot iniciado!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
