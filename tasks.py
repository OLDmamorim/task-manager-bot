"""
Funções de gestão de tarefas
"""
from database import get_db
from datetime import datetime


def create_task(user_id, title, description=None, priority='Média', category=None, 
                due_date=None, due_time=None, duration_minutes=60):
    """Criar nova tarefa"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tasks (user_id, title, description, priority, category, 
                          due_date, due_time, duration_minutes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, title, description, priority, category, due_date, due_time, duration_minutes))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return task_id


def get_user_tasks(user_id, status=None, category=None, due_date=None):
    """Obter tarefas do utilizador"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM tasks WHERE user_id = ?'
    params = [user_id]
    
    if status:
        query += ' AND status = ?'
        params.append(status)
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    if due_date:
        query += ' AND due_date = ?'
        params.append(due_date)
    
    query += ' ORDER BY category ASC, CASE priority WHEN "Alta" THEN 1 WHEN "Média" THEN 2 ELSE 3 END, due_date ASC, created_at DESC'
    
    cursor.execute(query, params)
    tasks = cursor.fetchall()
    conn.close()
    
    return tasks


def get_task_by_id(task_id):
    """Obter tarefa por ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    conn.close()
    return task


def complete_task(task_id):
    """Marcar tarefa como concluída"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE tasks 
        SET status = 'Concluída', completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (task_id,))
    
    conn.commit()
    conn.close()


def delete_task(task_id):
    """Apagar tarefa"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()


def update_task(task_id, **kwargs):
    """Atualizar tarefa"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Construir query dinâmica
    fields = []
    values = []
    
    for key, value in kwargs.items():
        if value is not None:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if not fields:
        conn.close()
        return
    
    query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
    values.append(task_id)
    
    cursor.execute(query, values)
    conn.commit()
    conn.close()


def get_user_categories(user_id):
    """Obter categorias do utilizador"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories WHERE user_id = ? ORDER BY name', (user_id,))
    categories = cursor.fetchall()
    conn.close()
    return categories


def add_category(user_id, name, emoji='📁'):
    """Adicionar categoria"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO categories (user_id, name, emoji)
            VALUES (?, ?, ?)
        ''', (user_id, name, emoji))
        conn.commit()
        success = True
    except:
        success = False
    
    conn.close()
    return success


def delete_category(category_id):
    """Apagar categoria"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()


def get_stats(user_id):
    """Obter estatísticas do utilizador"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total de tarefas
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ?', (user_id,))
    total = cursor.fetchone()[0]
    
    # Tarefas concluídas
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = "Concluída"', (user_id,))
    completed = cursor.fetchone()[0]
    
    # Tarefas pendentes
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = "Pendente"', (user_id,))
    pending = cursor.fetchone()[0]
    
    # Taxa de conclusão
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    # Tarefas concluídas hoje
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) FROM tasks 
        WHERE user_id = ? AND status = "Concluída" 
        AND DATE(completed_at) = ?
    ''', (user_id, today))
    completed_today = cursor.fetchone()[0]
    
    # Tarefas concluídas esta semana
    cursor.execute('''
        SELECT COUNT(*) FROM tasks 
        WHERE user_id = ? AND status = "Concluída" 
        AND DATE(completed_at) >= DATE('now', '-7 days')
    ''', (user_id,))
    completed_week = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total,
        'completed': completed,
        'pending': pending,
        'completion_rate': completion_rate,
        'completed_today': completed_today,
        'completed_week': completed_week,
    }
