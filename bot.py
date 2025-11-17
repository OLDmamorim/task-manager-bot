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
/tarefas - Ver tarefas pendentes
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
/tarefas - Ver tarefas pendentes
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
    """Comando /tarefas - Listar tarefas pendentes"""
    user_id = update.effective_user.id
    tasks = get_user_tasks(user_id, status='Pendente')
    
    if not tasks:
        await update.message.reply_text("✅ Você não tem tarefas pendentes!")
        return
    
    text = f"📋 **Tarefas Pendentes** ({len(tasks)})\n\n"
    
    for task in tasks:
        priority_emoji = get_priority_emoji(task['priority'])
        title = task['title']
        
        # Data
        date_info = ""
        if task['due_date']:
            relative = get_relative_date_text(task['due_date'])
            date_str = format_date_pt(task['due_date'])
            
            if is_overdue(task['due_date'], task['due_time']):
                date_info = f"⚠️ Atrasada - {date_str}"
            else:
                date_info = f"📅 {relative} ({date_str})"
        
        text += f"{priority_emoji} **{title}**\n"
        if date_info:
            text += f"   {date_info}\n"
        if task['category']:
            text += f"   🏷️ {task['category']}\n"
        text += f"   ID: `{task['id']}`\n\n"
    
    text += "\n💡 Use /concluir para marcar como concluída"
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def hoje_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /hoje - Tarefas para hoje"""
    user_id = update.effective_user.id
    today = datetime.now().strftime('%Y-%m-%d')
    tasks = get_user_tasks(user_id, status='Pendente', due_date=today)
    
    if not tasks:
        await update.message.reply_text("✅ Não há tarefas para hoje!")
        return
    
    text = f"📅 **Tarefas de Hoje** ({len(tasks)})\n\n"
    
    for task in tasks:
        priority_emoji = get_priority_emoji(task['priority'])
        text += f"{priority_emoji} **{task['title']}**\n"
        if task['due_time']:
            text += f"   ⏰ {task['due_time']}\n"
        if task['category']:
            text += f"   🏷️ {task['category']}\n"
        text += f"   ID: `{task['id']}`\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')


# ==================== CONCLUIR TAREFA ====================

async def concluir_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /concluir"""
    user_id = update.effective_user.id
    tasks = get_user_tasks(user_id, status='Pendente')
    
    if not tasks:
        await update.message.reply_text("✅ Não há tarefas pendentes!")
        return
    
    keyboard = []
    for task in tasks[:10]:  # Limitar a 10
        priority_emoji = get_priority_emoji(task['priority'])
        keyboard.append([InlineKeyboardButton(
            f"{priority_emoji} {task['title']}",
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
    tasks = get_user_tasks(user_id, status='Pendente')
    
    if not tasks:
        await update.message.reply_text("Não há tarefas para apagar!")
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
    
    # Concluir tarefa
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
        
        text = f"✅ Prioridade: **{priority}**\n\n📅 Envie a **data de vencimento** (DD/MM/AAAA) ou \"não\" para pular:"
        await query.edit_message_text(text, parse_mode='Markdown')
        return
    
    # Google Calendar
    if data.startswith("gcal_"):
        response = data.replace("gcal_", "")
        
        if response == "yes":
            # Gerar link Google Calendar
            task_data = context.user_data.get('task_data', {})
            
            if task_data.get('due_date') and task_data.get('due_time'):
                link = generate_google_calendar_link(
                    title=task_data['title'],
                    description=task_data.get('description', ''),
                    start_date=task_data['due_date'],
                    start_time=task_data['due_time'],
                    duration_minutes=task_data.get('duration', 60)
                )
                
                text = f"📆 **Adicionar ao Google Calendar**\n\n[Clique aqui para adicionar]({link})"
                await query.edit_message_text(text, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ Tarefa sem data/hora definida!")
        else:
            await query.edit_message_text("✅ Tarefa criada com sucesso!")
        
        # Limpar context
        context.user_data.pop('creating_task', None)
        context.user_data.pop('task_data', None)
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
    
    # Criar tarefa - Data
    if context.user_data.get('creating_task') and 'priority' in context.user_data.get('task_data', {}) and 'due_date' not in context.user_data.get('task_data', {}):
        if text.lower() == 'não' or text.lower() == 'nao':
            # Sem data - criar tarefa
            task_data = context.user_data['task_data']
            task_id = create_task(
                user_id=update.effective_user.id,
                title=task_data['title'],
                priority=task_data['priority']
            )
            
            await update.message.reply_text(
                f"✅ **Tarefa criada!**\n\n"
                f"📋 {task_data['title']}\n"
                f"⚡ Prioridade: {task_data['priority']}\n"
                f"ID: `{task_id}`",
                parse_mode='Markdown'
            )
            
            context.user_data.pop('creating_task', None)
            context.user_data.pop('task_data', None)
            return
        
        # Validar data
        from utils import parse_date_pt
        due_date = parse_date_pt(text)
        
        if not due_date:
            await update.message.reply_text("❌ Data inválida! Use o formato DD/MM/AAAA ou envie \"não\"")
            return
        
        context.user_data['task_data']['due_date'] = due_date
        
        await update.message.reply_text("⏰ Envie a **hora** (HH:MM) ou \"não\" para pular:")
        return
    
    # Criar tarefa - Hora
    if context.user_data.get('creating_task') and 'due_date' in context.user_data.get('task_data', {}) and 'due_time' not in context.user_data.get('task_data', {}):
        if text.lower() == 'não' or text.lower() == 'nao':
            # Sem hora - criar tarefa
            task_data = context.user_data['task_data']
            task_id = create_task(
                user_id=update.effective_user.id,
                title=task_data['title'],
                priority=task_data['priority'],
                due_date=task_data['due_date']
            )
            
            await update.message.reply_text(
                f"✅ **Tarefa criada!**\n\n"
                f"📋 {task_data['title']}\n"
                f"⚡ Prioridade: {task_data['priority']}\n"
                f"📅 Data: {format_date_pt(task_data['due_date'])}\n"
                f"ID: `{task_id}`",
                parse_mode='Markdown'
            )
            
            context.user_data.pop('creating_task', None)
            context.user_data.pop('task_data', None)
            return
        
        # Validar hora
        try:
            datetime.strptime(text, '%H:%M')
            context.user_data['task_data']['due_time'] = text
        except:
            await update.message.reply_text("❌ Hora inválida! Use o formato HH:MM ou envie \"não\"")
            return
        
        # Criar tarefa com data e hora
        task_data = context.user_data['task_data']
        task_id = create_task(
            user_id=update.effective_user.id,
            title=task_data['title'],
            priority=task_data['priority'],
            due_date=task_data['due_date'],
            due_time=task_data['due_time']
        )
        
        # Perguntar sobre Google Calendar
        keyboard = [
            [InlineKeyboardButton("✅ Sim", callback_data="gcal_yes")],
            [InlineKeyboardButton("❌ Não", callback_data="gcal_no")],
        ]
        
        await update.message.reply_text(
            f"✅ **Tarefa criada!**\n\n"
            f"📋 {task_data['title']}\n"
            f"⚡ Prioridade: {task_data['priority']}\n"
            f"📅 {format_date_pt(task_data['due_date'])} às {task_data['due_time']}\n"
            f"ID: `{task_id}`\n\n"
            f"📆 **Adicionar ao Google Calendar?**",
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
        BotCommand("tarefas", "Ver tarefas pendentes"),
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
