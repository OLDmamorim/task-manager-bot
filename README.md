# 📋 Task Manager Bot

Bot de Telegram para gestão de tarefas com integração Google Calendar.

## 🚀 Funcionalidades

### Gestão de Tarefas
- ✅ Criar tarefas com título, descrição e prioridade
- ✅ Listar tarefas (todas, pendentes, concluídas)
- ✅ Marcar como concluída
- ✅ Editar tarefas
- ✅ Apagar tarefas
- ✅ Adicionar tags/categorias

### Lembretes e Prazos
- ⏰ Definir data/hora de vencimento
- 🔔 Lembretes automáticos
- 📅 Ver tarefas por data (hoje, amanhã, esta semana)

### Google Calendar
- 📆 Link direto para adicionar tarefa ao Google Calendar
- ⏱️ Duração configurável
- 🔗 Pré-preenchimento automático

### Produtividade
- 📊 Estatísticas de conclusão
- 🎯 Metas diárias/semanais
- 🏆 Streaks de produtividade

## 📦 Instalação

```bash
pip install -r requirements.txt
python bot.py
```

## 🔧 Configuração

Criar ficheiro `.env`:
```
TELEGRAM_BOT_TOKEN=seu_token_aqui
```

## 🎯 Comandos

- `/start` - Iniciar o bot
- `/nova_tarefa` - Criar nova tarefa
- `/tarefas` - Ver todas as tarefas
- `/hoje` - Tarefas para hoje
- `/concluir` - Marcar tarefa como concluída
- `/editar` - Editar tarefa
- `/apagar_tarefa` - Apagar tarefa
- `/categorias` - Gerir categorias
- `/stats` - Ver estatísticas

## 🛠️ Tecnologias

- Python 3.11
- python-telegram-bot
- SQLite
- Google Calendar API (links diretos)

## 📝 Licença

MIT License
