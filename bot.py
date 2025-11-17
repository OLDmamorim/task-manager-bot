"""
Task Manager Bot - Bot de Gestão de Tarefas
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
    delete_task, update_task, get_user_categories, get_stats
)
from utils import (
    format_date_pt, get_priority_emoji, get_status_emoji,
    generate_google_calendar_link, is_overdue, get_relative_date_text
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


# ==================== COMANDOS BÁSICOS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user = update.effective_user
    register_user(user.id, user.username, user.first_name, user.last_name)
    add_default_categories(user.id)
    
    text = f"""
👋 **Olá, {user.first_name}!**

Bem-vindo ao **Task Manager Bot**!

📋 **Comandos principais:**
/nova_tarefa - Criar tarefa
/tarefas_ativas - Ver tarefas pendentes com checkboxes
/tarefas - Ver todas as tarefas
/hoje - Tarefas de hoje
/stats - Estatísticas

Digite /help para ver todos os comandos!
"""
    await update.message.reply_text(text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    text = """
📚 **Comandos Disponíveis:**

**Tarefas:**
/nova_tarefa - Criar nova tarefa
/tarefas_ativas - Ver tarefas pendentes (com checkboxes)
/tarefas - Ver todas as tarefas
/hoje - Tarefas para hoje
/concluir - Marcar como concluída
/apagar_tarefa - Apagar tarefa

**Estatísticas:**
/stats - Ver estatísticas

**Ajuda:**
/help - Mostrar esta mensagem
"""
    await update.message.reply_text(text, parse_mode='Markdown')


# ==================== CRIAR TAREFA ====================

async def nova_tarefa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /nova_tarefa"""
    context.user_data['creating_task'] = True
    context.user_data['task_data'] = {}
    
    text = "📝 **Criar Nova Tarefa**\n\nEnvie o **título** da tarefa:"
    await update.message.reply_text(text, parse_mode='Markdown')


# ==================== LISTAR TAREFAS ====================

async def tarefas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /tarefas - Listar todas as tarefas"""
    user_id = update.effective_user.id
    tasks = get_user_tasks(user_id, completed=False)
    
    if not tasks:
        await update.message.reply_text("📭 Não tens tarefas pendentes!")
        return
    
    text = "📋 **Tarefas Pendentes:**\n\n"
    
    for task in tasks:
        status = get_status_emoji(task)
        priority = get_priority_emoji(task['priority'])
        
        text += f"{status} {priority} **{task['title']}**\n"
        
        if task['due_date']:
            relative = get_relative_date_text(task['due_date'])
            text += f"   📅 {relative}\n"
        
        text += f"   ID: `{task['id']}`\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def tarefas_ativas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /tarefas_ativas - Listar tarefas pendentes com checkboxes"""
    user_id = update.effective_user.id
    tasks = get_user_tasks(user_id, completed=False)
    
    if not tasks:
        await update.message.reply_text("📭 Não tens tarefas pendentes!")
        return
    
    keyboard = []
    
    for task in tasks[:15]:  # Limitar a 15 tarefas
        priority = get_priority_emoji(task['priority'])
        title = task['title'][:40]  # Limitar título
        
        # Adicionar info de data se existir
        date_info = ""
        if task['due_date']:
            relative = get_relative_date_text(task['due_date'])
            date_info = f" - {relative}"
        
        button_text = f"☐ {priority} {title}{date_info}"
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"check_{task['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Fechar", callback_data="cancel")])
    
    await update.message.reply_text(
        "✅ **Tarefas Ativas**\n\nClica para marcar como concluída:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def hoje_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /hoje - Tarefas de hoje"""
    user_id = update.effective_user.id
    tasks = get_user_tasks(user_id, completed=False)
    
    today = datetime.now().date()
    today_tasks = [t for t in tasks if t['due_date'] and datetime.strptime(t['due_date'], '%Y-%m-%d').date() == today]
    
    if not today_tasks:
        await update.message.reply_text("📅 Não tens tarefas para hoje!")
        return
    
    text = "📅 **Tarefas de Hoje:**\n\n"
    
    for task in today_tasks:
        priority = get_priority_emoji(task['priority'])
        text += f"{priority} **{task['title']}**\n"
        text += f"   ID: `{task['id']}`\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')


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
        "✅ **Concluir Tarefa**\n\nSelecione a tarefa:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
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
        "🗑️ **Apagar Tarefa**\n\nSelecione a tarefa:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# ==================== ESTATÍSTICAS ====================

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stats"""
    user_id = update.effective_user.id
    stats = get_stats(user_id)
    
    text = f"""
📊 **Suas Estatísticas**

📋 Total de tarefas: **{stats['total']}**
✅ Concluídas: **{stats['completed']}**
⏳ Pendentes: **{stats['pending']}**
📈 Taxa de conclusão: **{stats['completion_rate']:.1f}%**

🎯 **Hoje:** {stats['completed_today']} concluída(s)
📅 **Esta semana:** {stats['completed_week']} concluída(s)
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')


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
    
    # Checkbox - Marcar como concluída (de /tarefas_ativas)
    if data.startswith("check_"):
        task_id = int(data.replace("check_", ""))
        task = get_task_by_id(task_id)
        
        if task:
            complete_task(task_id)
            await query.edit_message_text(
                f"✅ **Tarefa concluída!**\n\n📋 {task['title']}\n\n🎉 Parabéns!",
                parse_mode='Markdown'
            )
        return
    
    # Concluir tarefa (de /concluir)
    if data.startswith("complete_"):
        task_id = int(data.replace("complete_", ""))
        task = get_task_by_id(task_id)
        
        if task:
            complete_task(task_id)
            await query.edit_message_text(
                f"✅ **Tarefa concluída!**\n\n📋 {task['title']}\n\n🎉 Parabéns!",
                parse_mode='Markdown'
            )
        return
    
    # Apagar tarefa
    if data.startswith("delete_"):
        task_id = int(data.replace("delete_", ""))
        task = get_task_by_id(task_id)
        
        if task:
            delete_task(task_id)
            await query.edit_message_text(
                f"🗑️ **Tarefa apagada!**\n\n📋 {task['title']}",
                parse_mode='Markdown'
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
            f"✅ Prioridade: **{priority}**\n\n📅 **Escolhe a data de vencimento:**",
            reply_markup=calendar,
            parse_mode='Markdown'
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
            # Ignorar cliques em botões não interativos
            return
        
        elif action in ["prev", "next"]:
            # Navegar para mês anterior/próximo
            calendar = get_month_calendar(year, month)
            context.user_data['cal_year'] = year
            context.user_data['cal_month'] = month
            
            await query.edit_message_reply_markup(reply_markup=calendar)
            return
        
        elif action == "select":
            # Data selecionada
            context.user_data['task_data']['due_date'] = date
            
            # Criar tarefa
            task_data = context.user_data['task_data']
            task_id = create_task(
                user_id=query.from_user.id,
                title=task_data['title'],
                priority=task_data['priority'],
                due_date=task_data['due_date']
            )
            
            # Perguntar sobre Google Calendar
            keyboard = [
                [InlineKeyboardButton("✅ Sim", callback_data="gcal_yes")],
                [InlineKeyboardButton("❌ Não", callback_data="gcal_no")],
            ]
            
            await query.edit_message_text(
                f"✅ **Tarefa criada!**\n\n"
                f"📋 {task_data['title']}\n"
                f"⚡ Prioridade: {task_data['priority']}\n"
                f"📅 Data: {format_date_pt(task_data['due_date'])}\n"
                f"ID: `{task_id}`\n\n"
                f"📆 **Adicionar ao Google Calendar?**",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        return
    
    # Google Calendar
    if data.startswith("gcal_"):
        response = data.replace("gcal_", "")
        
        if response == "yes":
            # Gerar link Google Calendar
            task_data = context.user_data.get('task_data', {})
            
            if task_data.get('due_date'):
                link = generate_google_calendar_link(
                    title=task_data['title'],
                    description='',
                    start_date=task_data['due_date'],
                    start_time='09:00',  # Hora padrão
                    duration_minutes=60
                )
                
                text = f"📆 **Adicionar ao Google Calendar**\n\n[Clique aqui para adicionar]({link})"
                await query.edit_message_text(text, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ Tarefa sem data definida!")
        else:
            await query.edit_message_text("✅ Tarefa criada com sucesso!")
        
        # Limpar context
        context.user_data.pop('creating_task', None)
        context.user_data.pop('task_data', None)
        context.user_data.pop('cal_year', None)
        context.user_data.pop('cal_month', None)
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
            "⚡ **Escolha a prioridade:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return


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
    
    # Configurar comandos
    app.post_init = setup_commands
    
    # Iniciar bot
    logger.info("🤖 Bot iniciado!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
