"""
Calendário inline simples para Telegram
"""
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_month_calendar(year, month):
    """Gera um calendário inline para o mês especificado"""
    # Nomes dos meses em português
    month_names = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    
    # Dias da semana
    weekdays = ["S", "T", "Q", "Q", "S", "S", "D"]
    
    # Primeiro dia do mês
    first_day = datetime(year, month, 1)
    
    # Último dia do mês
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Dia da semana do primeiro dia (0 = segunda, 6 = domingo)
    start_weekday = first_day.weekday()
    
    # Criar teclado
    keyboard = []
    
    # Cabeçalho com mês e ano
    keyboard.append([
        InlineKeyboardButton("◀️", callback_data=f"cal_prev_{year}_{month}"),
        InlineKeyboardButton(f"{month_names[month-1]} {year}", callback_data="cal_ignore"),
        InlineKeyboardButton("▶️", callback_data=f"cal_next_{year}_{month}"),
    ])
    
    # Dias da semana
    keyboard.append([InlineKeyboardButton(day, callback_data="cal_ignore") for day in weekdays])
    
    # Dias do mês
    week = []
    
    # Espaços vazios antes do primeiro dia
    for _ in range(start_weekday):
        week.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
    
    # Dias do mês
    for day in range(1, last_day.day + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        week.append(InlineKeyboardButton(str(day), callback_data=f"cal_select_{date_str}"))
        
        # Se completou a semana, adiciona ao teclado
        if len(week) == 7:
            keyboard.append(week)
            week = []
    
    # Preencher última semana se necessário
    if week:
        while len(week) < 7:
            week.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
        keyboard.append(week)
    
    # Botões de ação
    keyboard.append([
        InlineKeyboardButton("📭 SEM DATA", callback_data="cal_nodate"),
        InlineKeyboardButton("❌ Cancelar", callback_data="cal_cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def handle_calendar_callback(callback_data, current_year=None, current_month=None):
    """
    Processa callback do calendário
    Retorna: (action, year, month, date)
    - action: 'select', 'prev', 'next', 'cancel', 'ignore'
    - year, month: ano e mês atual
    - date: data selecionada (formato YYYY-MM-DD) ou None
    """
    if callback_data == "cal_ignore":
        return ("ignore", current_year, current_month, None)
    
    if callback_data == "cal_cancel":
        return ("cancel", None, None, None)
    
    if callback_data == "cal_nodate":
        return ("nodate", None, None, None)
    
    parts = callback_data.split("_")
    
    if parts[1] == "select":
        # Data selecionada
        date_str = parts[2]
        return ("select", None, None, date_str)
    
    elif parts[1] == "prev":
        # Mês anterior
        year = int(parts[2])
        month = int(parts[3])
        
        if month == 1:
            return ("prev", year - 1, 12, None)
        else:
            return ("prev", year, month - 1, None)
    
    elif parts[1] == "next":
        # Próximo mês
        year = int(parts[2])
        month = int(parts[3])
        
        if month == 12:
            return ("next", year + 1, 1, None)
        else:
            return ("next", year, month + 1, None)
    
    return ("ignore", current_year, current_month, None)
