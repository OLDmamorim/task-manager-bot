"""
Funções auxiliares
"""
from datetime import datetime, timedelta
from urllib.parse import quote


def format_date_pt(date_str):
    """Formatar data para português (DD/MM/YYYY)"""
    if not date_str:
        return "Sem data"
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except:
        return date_str


def parse_date_pt(date_str):
    """Converter data PT (DD/MM/YYYY) para formato ISO (YYYY-MM-DD)"""
    try:
        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        return date_obj.strftime('%Y-%m-%d')
    except:
        return None


def get_priority_emoji(priority):
    """Obter emoji para prioridade"""
    emojis = {
        'Alta': '🔴',
        'Média': '🟡',
        'Baixa': '🟢'
    }
    return emojis.get(priority, '⚪')


def get_status_emoji(status):
    """Obter emoji para status"""
    emojis = {
        'Pendente': '⏳',
        'Concluída': '✅',
        'Atrasada': '⚠️'
    }
    return emojis.get(status, '❓')


def generate_google_calendar_link(title, description, start_date, start_time, duration_minutes):
    """
    Gerar link do Google Calendar para adicionar evento
    
    Args:
        title: Título do evento
        description: Descrição do evento
        start_date: Data de início (YYYY-MM-DD)
        start_time: Hora de início (HH:MM)
        duration_minutes: Duração em minutos
    
    Returns:
        URL do Google Calendar
    """
    # Combinar data e hora
    start_datetime = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
    end_datetime = start_datetime + timedelta(minutes=duration_minutes)
    
    # Formato: YYYYMMDDTHHmmSS
    start_str = start_datetime.strftime('%Y%m%dT%H%M%S')
    end_str = end_datetime.strftime('%Y%m%dT%H%M%S')
    
    # Construir URL
    base_url = "https://calendar.google.com/calendar/render"
    params = {
        'action': 'TEMPLATE',
        'text': title,
        'details': description or '',
        'dates': f"{start_str}/{end_str}",
    }
    
    # Montar query string
    query = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
    
    return f"{base_url}?{query}"


def is_overdue(due_date, due_time=None):
    """Verificar se tarefa está atrasada"""
    if not due_date:
        return False
    
    try:
        if due_time:
            task_datetime = datetime.strptime(f"{due_date} {due_time}", '%Y-%m-%d %H:%M')
        else:
            task_datetime = datetime.strptime(due_date, '%Y-%m-%d')
            task_datetime = task_datetime.replace(hour=23, minute=59)
        
        return datetime.now() > task_datetime
    except:
        return False


def get_relative_date_text(date_str):
    """Obter texto relativo para data (Hoje, Amanhã, etc.)"""
    if not date_str:
        return ""
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        if date_obj == today:
            return "Hoje"
        elif date_obj == tomorrow:
            return "Amanhã"
        elif date_obj < today:
            days_ago = (today - date_obj).days
            return f"Há {days_ago} dia{'s' if days_ago > 1 else ''}"
        else:
            days_left = (date_obj - today).days
            return f"Em {days_left} dia{'s' if days_left > 1 else ''}"
    except:
        return ""
