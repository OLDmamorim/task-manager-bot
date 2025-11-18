"""
Gestão da base de dados PostgreSQL (Neon)
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Connection string do Neon
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_ivMOZA7RzWD3@ep-odd-surf-agzhu0h2.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require')


def get_db():
    """Conectar à base de dados PostgreSQL"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def init_db():
    """Inicializar base de dados com tabelas"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabela de utilizadores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de tarefas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'Média',
            category TEXT,
            due_date TEXT,
            due_time TEXT,
            duration_minutes INTEGER DEFAULT 60,
            status TEXT DEFAULT 'Pendente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela de categorias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '📁',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
            UNIQUE(user_id, name)
        )
    ''')
    
    # Índices para melhor performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_user_id ON categories(user_id)')
    
    conn.commit()
    conn.close()
    print("✅ Base de dados PostgreSQL inicializada com sucesso!")


def register_user(telegram_id, username=None, first_name=None, last_name=None):
    """Registar ou atualizar utilizador"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar se o utilizador já existe
    cursor.execute('SELECT telegram_id FROM users WHERE telegram_id = %s', (telegram_id,))
    exists = cursor.fetchone()
    
    if exists:
        # Atualizar dados do utilizador existente
        cursor.execute('''
            UPDATE users 
            SET username = %s, first_name = %s, last_name = %s
            WHERE telegram_id = %s
        ''', (username, first_name, last_name, telegram_id))
    else:
        # Inserir novo utilizador
        cursor.execute('''
            INSERT INTO users (telegram_id, username, first_name, last_name)
            VALUES (%s, %s, %s, %s)
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
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, name) DO NOTHING
            ''', (user_id, name, emoji))
        except Exception as e:
            # Categoria já existe - ignorar
            pass
    
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
