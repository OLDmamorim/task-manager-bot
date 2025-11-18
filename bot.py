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


def generate_google_calendar_link(title, date, time=None, category=None):
    """Gerar link para adicionar evento ao Google Calendar"""
    from urllib.parse import quote
    from datetime import datetime, timedelta
    
    # Formato: YYYYMMDDTHHMMSSZ (com hora)
    date_formatted = date.replace('-', '')
    
    # Se não houver hora, usar 09:00 por padrão
    if not time:
        time = "09:00"
    
    # Converter hora para formato do Google Calendar
    hour, minute = time.split(':')
    start_hour = int(hour)
    end_hour = start_hour + 1  # Duração de 1 hora
    
    # Usar formato sem timezone (deixar o Google Calendar interpretar)
    start_datetime = f"{date_formatted}T{start_hour:02d}{minute}00"
    end_datetime = f"{date_formatted}T{end_hour:02d}{minute}00"
    
    # Título do evento
    event_title = quote(title)
    
    # Descrição (incluir categoria se existir)
    description = ""
    if category:
        description = quote(f"Categoria: {category}")
    
    # URL do Google Calendar
    # Formato: https://calendar.google.com/calendar/render?action=TEMPLATE&text=TITLE&dates=START/END&details=DESCRIPTION
    url = f"https://calendar.google.com/calendar/render?action=TEMPLATE"
    url += f"&text={event_title}"
    url += f"&dates={start_datetime}/{end_datetime}"
    
    if description:
        url += f"&details={description}"
    
    return url


def format_task_text(task):
    """Formatar texto de uma tarefa"""
    priority = get_priority_emoji(task['priority'])
    title = task['title']
    
    text = f"{priority} <b>{title}</b>\n"
    
    # Categoria
    if task['category'] and task['category'] != '':
        text += f"   🏷️ {task['category']}\n"
    
    # Data
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
    
    # Menu inline com atalhos rápidos
    keyboard = [
        [InlineKeyboardButton("➕ Nova Tarefa", callback_data="menu_nova_tarefa")],
        [InlineKeyboardButton("📋 Ver Tarefas", callback_data="menu_tarefas"),
         InlineKeyboardButton("📅 Hoje", callback_data="menu_hoje")],
        [InlineKeyboardButton("🏷️ Categorias", callback_data="menu_categorias"),
         InlineKeyboardButton("📊 Stats", callback_data="menu_stats")],
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


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
    tasks = get_user_tasks(user_id, status='Pendente')
    
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
    tasks = get_user_tasks(user_id, status='Pendente')
    
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
    tasks = get_user_tasks(user_id, status='Pendente')
    
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
    tasks = get_user_tasks(user_id, status='Pendente')
    
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
    tasks = get_user_tasks(user_id, status='Pendente')
    
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

async def categoria_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /categoria - Filtrar tarefas por categoria"""
    user_id = update.effective_user.id
    from tasks import get_user_categories
    
    categories = get_user_categories(user_id)
    
    if not categories:
        await update.message.reply_text(
            "❌ Não tens categorias criadas.",
            parse_mode='HTML'
        )
        return
    
    # Criar teclado com categorias
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(
            f"{cat['emoji']} {cat['name']}",
            callback_data=f"filter_cat_{cat['id']}"
        )])
    
    # Botão para ver todas
    keyboard.append([InlineKeyboardButton(
        "📋 Ver Todas as Tarefas",
        callback_data="filter_cat_all"
    )])
    
    await update.message.reply_text(
        "🏷️ <b>Filtrar tarefas por categoria:</b>\n\nEscolhe uma categoria:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


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
    
    # Menu inline - Atalhos rápidos
    if data.startswith("menu_"):
        user_id = query.from_user.id
        
        if data == "menu_nova_tarefa":
            await query.message.reply_text("📝 Use o comando /nova_tarefa para criar uma nova tarefa.")
            return
        
        elif data == "menu_tarefas":
            tasks = get_user_tasks(user_id, status='Pendente')
            if not tasks:
                await query.edit_message_text("✅ Nenhuma tarefa pendente!")
                return
            
            text = "📋 <b>Tarefas Pendentes:</b>\n\n"
            for task in tasks:
                text += format_task_text(task) + "\n"
            
            await query.edit_message_text(text, parse_mode='HTML')
            return
        
        elif data == "menu_hoje":
            from datetime import date
            today = date.today().strftime('%Y-%m-%d')
            tasks = get_user_tasks(user_id, status='Pendente', due_date=today)
            
            if not tasks:
                await query.edit_message_text("✅ Nenhuma tarefa para hoje!")
                return
            
            text = "📅 <b>Tarefas de Hoje:</b>\n\n"
            for task in tasks:
                text += format_task_text(task) + "\n"
            
            await query.edit_message_text(text, parse_mode='HTML')
            return
        
        elif data == "menu_categorias":
            from tasks import get_user_categories
            categories = get_user_categories(user_id)
            
            if not categories:
                await query.edit_message_text("❌ Não tens categorias criadas.")
                return
            
            keyboard = []
            for cat in categories:
                keyboard.append([InlineKeyboardButton(
                    f"{cat['emoji']} {cat['name']}",
                    callback_data=f"filter_cat_{cat['id']}"
                )])
            keyboard.append([InlineKeyboardButton(
                "📋 Ver Todas as Tarefas",
                callback_data="filter_cat_all"
            )])
            
            await query.edit_message_text(
                "🏷️ <b>Filtrar tarefas por categoria:</b>\n\nEscolhe uma categoria:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        elif data == "menu_stats":
            stats = get_stats(user_id)
            text = f"""
📊 <b>Estatísticas:</b>

📋 Total de tarefas: {stats['total']}
✅ Concluídas: {stats['completed']}
⏳ Pendentes: {stats['pending']}
📅 Para hoje: {stats['today']}
🔥 Taxa de conclusão: {stats['completion_rate']:.1f}%
"""
            await query.edit_message_text(text, parse_mode='HTML')
            return
    
    # Filtrar por categoria
    if data.startswith("filter_cat_"):
        user_id = query.from_user.id
        
        if data == "filter_cat_all":
            # Mostrar todas as tarefas
            tasks = get_user_tasks(user_id, status='Pendente')
            title = "📋 <b>Todas as Tarefas Pendentes:</b>"
        else:
            # Filtrar por categoria específica
            cat_id = int(data.replace("filter_cat_", ""))
            from tasks import get_user_categories
            categories = get_user_categories(user_id)
            category = next((cat for cat in categories if cat['id'] == cat_id), None)
            
            if not category:
                await query.edit_message_text("❌ Categoria não encontrada.")
                return
            
            # Obter tarefas da categoria
            tasks = get_user_tasks(user_id, status='Pendente', category=category['name'])
            title = f"🏷️ <b>Tarefas: {category['emoji']} {category['name']}</b>"
        
        if not tasks:
            await query.edit_message_text(
                f"{title}\n\n✅ Nenhuma tarefa pendente!",
                parse_mode='HTML'
            )
            return
        
        # Formatar lista de tarefas
        text = f"{title}\n\n"
        for task in tasks:
            text += format_task_text(task) + "\n"
        
        await query.edit_message_text(text, parse_mode='HTML')
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
    
    # Concluir tarefa do lembrete diário
    if data.startswith("daily_complete_"):
        task_id = int(data.replace("daily_complete_", ""))
        task = get_task_by_id(task_id)
        
        if task:
            complete_task(task_id)
            
            # Editar a mensagem removendo a tarefa concluída
            user_id = query.from_user.id
            remaining_tasks = get_user_tasks(user_id, status='Pendente')
            
            if not remaining_tasks:
                # Todas as tarefas concluídas
                await query.edit_message_text(
                    f"🎉 <b>Parabéns!</b>\n\nTodas as tarefas foram concluídas!\n✅ {task['title']}",
                    parse_mode='HTML'
                )
            else:
                # Atualizar lista sem a tarefa concluída
                text = "🌅 <b>Bom dia!</b>\n\n"
                text += "📋 <b>Tarefas Pendentes:</b>\n\n"
                
                keyboard = []
                for t in remaining_tasks:
                    priority = get_priority_emoji(t['priority'])
                    title = t['title']
                    task_text = f"{priority} {title}"
                    
                    if t['category'] and t['category'] != '':
                        task_text += f" 🏷️ {t['category']}"
                    
                    if t['due_date']:
                        try:
                            date_obj = datetime.strptime(t['due_date'], '%Y-%m-%d')
                            today = datetime.now().date()
                            task_date = date_obj.date()
                            
                            if task_date == today:
                                task_text += " 📅 Hoje"
                            elif task_date == today + timedelta(days=1):
                                task_text += " 📅 Amanhã"
                            elif task_date < today:
                                days = (today - task_date).days
                                task_text += f" ⚠️ Atrasada {days}d"
                        except:
                            pass
                    
                    keyboard.append([InlineKeyboardButton(
                        f"☐ {task_text}",
                        callback_data=f"daily_complete_{t['id']}"
                    )])
                
                text += f"\n✅ <i>{task['title']} concluída!</i>"
                
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
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
    
    # Hora (após selecionar data)
    if data.startswith("time_"):
        # Guardar hora selecionada
        if data == "time_none":
            context.user_data['task_data']['time'] = None
        else:
            time = data.replace("time_", "")
            context.user_data['task_data']['time'] = time
        
        # Mostrar seleção de categoria
        user_id = context.user_data.get('user_id')
        from tasks import get_user_categories
        categories = get_user_categories(user_id)
        
        keyboard = []
        for cat in categories:
            keyboard.append([InlineKeyboardButton(
                f"{cat['emoji']} {cat['name']}",
                callback_data=f"category_{cat['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ Sem categoria", callback_data="category_none")])
        
        await query.edit_message_text(
            f"🏷️ <b>Escolha a categoria:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return
    
    # Categoria
    if data.startswith("category_"):
        task_data = context.user_data['task_data']
        user_id = context.user_data.get('user_id')
        
        # Obter categoria selecionada
        if data == "category_none":
            category = None
            category_name = "Sem categoria"
        else:
            category_id = int(data.replace("category_", ""))
            from tasks import get_user_categories
            categories = get_user_categories(user_id)
            category = next((cat['name'] for cat in categories if cat['id'] == category_id), None)
            category_name = category
        
        # Criar tarefa
        task_id = create_task(
            user_id=user_id,
            title=task_data['title'],
            priority=task_data['priority'],
            due_date=task_data.get('due_date'),
            category=category
        )
        
        # Mensagem de confirmação
        text = f"✅ <b>Tarefa criada!</b>\n\n"
        text += f"📋 {task_data['title']}\n"
        text += f"⚡ Prioridade: {task_data['priority']}\n"
        
        if task_data.get('due_date'):
            date_formatted = datetime.strptime(task_data['due_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
            text += f"📅 Data: {date_formatted}\n"
        else:
            text += f"📭 Sem data\n"
        
        if category:
            text += f"🏷️ Categoria: {category_name}"
        
        # Adicionar botão de Google Calendar se houver data
        keyboard = None
        if task_data.get('due_date'):
            gcal_link = generate_google_calendar_link(
                title=task_data['title'],
                date=task_data['due_date'],
                time=task_data.get('time'),
                category=category
            )
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("📅 Adicionar ao Google Calendar", url=gcal_link)
            ]])
        
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Limpar context
        context.user_data.pop('creating_task', None)
        context.user_data.pop('task_data', None)
        context.user_data.pop('cal_year', None)
        context.user_data.pop('cal_month', None)
        context.user_data.pop('user_id', None)
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
            # Data selecionada - mostrar seleção de hora
            context.user_data['task_data']['due_date'] = date
            
            # Mostrar seleção de hora
            keyboard = []
            hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
            
            # Criar botões de hora em 2 colunas
            for i in range(0, len(hours), 2):
                row = []
                row.append(InlineKeyboardButton(hours[i], callback_data=f"time_{hours[i]}"))
                if i + 1 < len(hours):
                    row.append(InlineKeyboardButton(hours[i+1], callback_data=f"time_{hours[i+1]}"))
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("⏰ Sem hora específica", callback_data="time_none")])
            
            date_formatted = datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')
            
            await query.edit_message_text(
                f"✅ Data: <b>{date_formatted}</b>\n\n⏰ <b>Escolha a hora:</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return
        
        elif action == "nodate":
            # Sem data - mostrar categorias
            context.user_data['task_data']['due_date'] = None
            
            # Mostrar seleção de categoria
            user_id = context.user_data.get('user_id')
            from tasks import get_user_categories
            categories = get_user_categories(user_id)
            
            keyboard = []
            for cat in categories:
                keyboard.append([InlineKeyboardButton(
                    f"{cat['emoji']} {cat['name']}",
                    callback_data=f"category_{cat['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("❌ Sem categoria", callback_data="category_none")])
            
            await query.edit_message_text(
                f"📭 <b>Sem data definida</b>\n\n🏷️ <b>Escolha a categoria:</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
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


# ==================== DAILY REMINDER ====================

async def send_daily_tasks(context: ContextTypes.DEFAULT_TYPE):
    """Enviar tarefas pendentes diariamente para todos os utilizadores"""
    logger.info("🔔 Enviando lembretes diários...")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Obter todos os utilizadores
    cursor.execute('SELECT telegram_id FROM users')
    users = cursor.fetchall()
    conn.close()
    
    for user in users:
        user_id = user['telegram_id']
        
        try:
            # Obter tarefas pendentes
            tasks = get_user_tasks(user_id, status='Pendente')
            
            if not tasks:
                # Não enviar mensagem se não houver tarefas
                continue
            
            # Separar tarefas atrasadas e normais
            today = datetime.now().date()
            overdue_tasks = []
            regular_tasks = []
            
            for task in tasks:
                if task['due_date']:
                    try:
                        task_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                        if task_date < today:
                            overdue_tasks.append(task)
                        else:
                            regular_tasks.append(task)
                    except:
                        regular_tasks.append(task)
                else:
                    regular_tasks.append(task)
            
            # Criar mensagem
            text = "🌅 <b>Bom dia!</b>\n\n"
            
            # Alerta de tarefas atrasadas
            if overdue_tasks:
                text += f"🚨 <b>ATENÇÃO: {len(overdue_tasks)} tarefa(s) atrasada(s)!</b>\n\n"
            
            text += "📋 <b>Tarefas Pendentes:</b>\n\n"
            
            # Criar teclado com checkboxes
            keyboard = []
            
            # Adicionar tarefas atrasadas primeiro (com emoji 🚨)
            for task in overdue_tasks:
                title = task['title']
                
                # Linha da tarefa com emoji de alerta
                task_text = f"🚨 {title}"
                
                # Adicionar categoria se existir
                if task['category'] and task['category'] != '':
                    task_text += f" 🏷️ {task['category']}"
                
                # Adicionar dias de atraso
                if task['due_date']:
                    try:
                        date_obj = datetime.strptime(task['due_date'], '%Y-%m-%d')
                        today = datetime.now().date()
                        task_date = date_obj.date()
                        days = (today - task_date).days
                        task_text += f" ⚠️ Atrasada {days}d"
                    except:
                        pass
                
                # Botão com checkbox
                keyboard.append([InlineKeyboardButton(
                    f"☐ {task_text}",
                    callback_data=f"daily_complete_{task['id']}"
                )])
            
            # Adicionar tarefas regulares (normais)
            for task in regular_tasks:
                priority = get_priority_emoji(task['priority'])
                title = task['title']
                
                # Linha da tarefa
                task_text = f"{priority} {title}"
                
                # Adicionar categoria se existir
                if task['category'] and task['category'] != '':
                    task_text += f" 🏷️ {task['category']}"
                
                # Adicionar data se existir
                if task['due_date']:
                    try:
                        date_obj = datetime.strptime(task['due_date'], '%Y-%m-%d')
                        today = datetime.now().date()
                        task_date = date_obj.date()
                        
                        if task_date == today:
                            task_text += " 📅 Hoje"
                        elif task_date == today + timedelta(days=1):
                            task_text += " 📅 Amanhã"
                        else:
                            days = (task_date - today).days
                            task_text += f" 📅 Em {days}d"
                    except:
                        pass
                
                # Botão com checkbox
                keyboard.append([InlineKeyboardButton(
                    f"☐ {task_text}",
                    callback_data=f"daily_complete_{task['id']}"
                )])
            
            # Enviar mensagem
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
            logger.info(f"✅ Lembrete enviado para user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar lembrete para user {user_id}: {e}")
            continue


async def send_today_tasks(context: ContextTypes.DEFAULT_TYPE):
    """Enviar tarefas do dia às 9:00"""
    logger.info("🔔 Enviando tarefas do dia...")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Obter todos os utilizadores
    cursor.execute('SELECT telegram_id FROM users')
    users = cursor.fetchall()
    conn.close()
    
    today = datetime.now().date().strftime('%Y-%m-%d')
    
    for user in users:
        user_id = user['telegram_id']
        
        try:
            # Obter tarefas de hoje
            tasks = get_user_tasks(user_id, status='Pendente', due_date=today)
            
            if not tasks:
                # Não enviar se não houver tarefas para hoje
                continue
            
            # Criar mensagem
            text = f"🔔 <b>Lembrete: Tarefas de HOJE!</b>\n\n"
            text += f"📅 Tens <b>{len(tasks)} tarefa(s)</b> para hoje:\n\n"
            
            # Criar teclado com checkboxes
            keyboard = []
            
            for task in tasks:
                priority = get_priority_emoji(task['priority'])
                title = task['title']
                
                task_text = f"{priority} {title}"
                
                if task['category'] and task['category'] != '':
                    task_text += f" 🏷️ {task['category']}"
                
                keyboard.append([InlineKeyboardButton(
                    f"☐ {task_text}",
                    callback_data=f"daily_complete_{task['id']}"
                )])
            
            # Enviar mensagem
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
            logger.info(f"✅ Tarefas do dia enviadas para user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar tarefas do dia para user {user_id}: {e}")
            continue


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
        BotCommand("categoria", "Filtrar tarefas por categoria"),
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
    app.add_handler(CommandHandler('categoria', categoria_command))
    
    # Handlers
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    # Configurar comandos
    app.post_init = setup_commands
    
    # Agendar envio diário de tarefas às 8:30
    job_queue = app.job_queue
    job_queue.run_daily(
        send_daily_tasks,
        time=datetime.strptime('08:30', '%H:%M').time(),
        days=(0, 1, 2, 3, 4, 5, 6),  # Todos os dias da semana
        name='daily_tasks_reminder'
    )
    
    # Agendar envio de tarefas do dia às 9:00
    job_queue.run_daily(
        send_today_tasks,
        time=datetime.strptime('09:00', '%H:%M').time(),
        days=(0, 1, 2, 3, 4, 5, 6),  # Todos os dias da semana
        name='today_tasks_reminder'
    )
    
    # Iniciar bot
    logger.info("🤖 Bot iniciado!")
    logger.info("🔔 Lembrete diário agendado para 8:30")
    logger.info("🔔 Lembrete de tarefas do dia agendado para 9:00")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
