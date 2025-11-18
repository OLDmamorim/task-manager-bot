"""
Gestão da base de dados SQLite
"""
import sqlite3
import os
from datetime import datetime

DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "tasks.db")


def get_db():
    """Conectar à base de dados"""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializar base de dados com tabelas"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabela de utilizadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de tarefas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'Média',
            category TEXT,
            due_date TEXT,
            due_time TEXT,
            duration_minutes INTEGER DEFAULT 60,
            status TEXT DEFAULT 'Pendente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
        )
    ''')
    
    # Tabela de categorias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '📁',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, name),
            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
        )
    ''')
    
    # Inserir categorias padrão
    default_categories = [
        ('Trabalho', '💼'),
        ('Pessoal', '🏠'),
        ('Urgente', '🚨'),
        ('Estudos', '📚'),
        ('Saúde', '💪'),
    ]
    
    conn.commit()
    conn.close()
    print("✅ Base de dados inicializada com sucesso!")


def register_user(telegram_id, username=None, first_name=None, last_name=None):
    """Registar ou atualizar utilizador"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar se o utilizador já existe
    cursor.execute('SELECT telegram_id FROM users WHERE telegram_id = ?', (telegram_id,))
    exists = cursor.fetchone()
    
    if exists:
        # Atualizar dados do utilizador existente
        cursor.execute('''
            UPDATE users 
            SET username = ?, first_name = ?, last_name = ?
            WHERE telegram_id = ?
        ''', (username, first_name, last_name, telegram_id))
    else:
        # Inserir novo utilizador
        cursor.execute('''
            INSERT INTO users (telegram_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (telegram_id, username, first_name, last_name))
    
    conn.commit()
    conn.close()


def add_default_categories(user_id):
    """Adicionar categorias padrão para novo utilizador"""
    default_categories = [
        ('Barcelos', '📍'),
        ('Braga', '📍'),
        ('Calibragem', '🔧'),
        ('Famalicão', '📍'),
        ('Guimarães', '📍'),
        ('Mycar', '🚗'),
        ('Paços Ferreira', '📍'),
        ('Paredes', '📍'),
        ('Viana do Castelo', '📍'),
        ('Vila Verde', '📍'),
        ('Outros', '📋'),
    ]
    
    conn = get_db()
    cursor = conn.cursor()
    
    for name, emoji in default_categories:
        try:
            cursor.execute('''
                INSERT INTO categories (user_id, name, emoji)
                VALUES (?, ?, ?)
            ''', (user_id, name, emoji))
        except sqlite3.IntegrityError:
            # Categoria já existe
            pass
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
