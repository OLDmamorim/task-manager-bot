# 📋 Task Manager Bot - Resumo do Projeto

## ✅ Status: PRONTO PARA DEPLOY

### 🎯 Objetivo
Bot Telegram para gestão de tarefas pessoais com integração Google Calendar via links diretos (sem OAuth).

---

## 📦 Estrutura do Projeto

```
task-manager-bot/
├── bot.py              # Bot principal com todos os handlers
├── database.py         # Configuração SQLite e schema
├── tasks.py            # Funções de gestão de tarefas
├── utils.py            # Funções auxiliares (Google Calendar)
├── requirements.txt    # Dependências Python
├── .gitignore         # Ficheiros ignorados pelo Git
├── README.md          # Documentação do projeto
├── DEPLOY.md          # Guia de deploy no Railway
└── .env               # Variáveis de ambiente (NÃO commitado)
```

---

## 🔧 Tecnologias Utilizadas

- **Python 3.11+**
- **python-telegram-bot v20+** (async/await)
- **SQLite3** (base de dados)
- **Google Calendar** (integração via URL)

---

## 🗄️ Base de Dados

### Tabela: `tasks`
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'Média',
    category TEXT,
    due_date TEXT,
    completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

## 🤖 Comandos Implementados

### Gestão de Tarefas
| Comando | Descrição |
|---------|-----------|
| `/start` | Mensagem de boas-vindas e menu principal |
| `/nova_tarefa` | Criar nova tarefa (com opção Google Calendar) |
| `/tarefas` | Listar todas as tarefas |
| `/hoje` | Ver tarefas de hoje |
| `/concluir` | Marcar tarefa como concluída |
| `/editar` | Editar uma tarefa existente |
| `/apagar_tarefa` | Apagar uma tarefa |

### Organização
| Comando | Descrição |
|---------|-----------|
| `/categorias` | Gerir categorias/tags |
| `/stats` | Estatísticas de produtividade |

---

## ✨ Funcionalidades Principais

### 1. Criação de Tarefas
- ✅ Título e descrição
- ✅ Prioridade (Alta/Média/Baixa)
- ✅ Categoria/tag personalizada
- ✅ Data de vencimento
- ✅ **Integração Google Calendar** (pergunta automática)

### 2. Visualização
- ✅ Lista completa de tarefas
- ✅ Filtro por pendentes/concluídas
- ✅ Tarefas de hoje
- ✅ Indicadores visuais (✅ ⏰ 🔴 🟡 🟢)

### 3. Gestão
- ✅ Marcar como concluída
- ✅ Editar título, descrição, prioridade, categoria, data
- ✅ Apagar tarefas
- ✅ Gerir categorias

### 4. Estatísticas
- ✅ Total de tarefas
- ✅ Tarefas concluídas
- ✅ Tarefas pendentes
- ✅ Taxa de conclusão
- ✅ Tarefas por categoria

### 5. Google Calendar
- ✅ Link direto (sem OAuth)
- ✅ Evento pré-preenchido
- ✅ Título, descrição e data automáticos
- ✅ Um clique para adicionar

---

## 🚀 Deploy

### GitHub Repository
**URL:** https://github.com/OLDmamorim/task-manager-bot

### Bot Token
```
8428607015:AAG-Ag9Rhj-PyCqoBHA0k0GhjsPRoNWrUpw
```

### Railway Deploy
1. Criar novo projeto no Railway
2. Conectar repositório: `OLDmamorim/task-manager-bot`
3. Adicionar variável: `BOT_TOKEN=8428607015:AAG-Ag9Rhj-PyCqoBHA0k0GhjsPRoNWrUpw`
4. Deploy automático! 🎉

**Guia completo:** Ver `DEPLOY.md`

---

## 📊 Comparação com Volante Minho Bot

| Aspeto | Volante Minho Bot | Task Manager Bot |
|--------|-------------------|------------------|
| **Objetivo** | Gestão de pedidos de lojas | Gestão de tarefas pessoais |
| **Utilizadores** | Admin + Múltiplas lojas | Utilizador individual |
| **Base de Dados** | Pedidos, bloqueios, utilizadores | Tarefas |
| **Calendário** | Visualização mensal | Google Calendar |
| **Deploy** | ✅ Railway (ativo) | ⏳ Pronto para deploy |
| **Status** | ✅ COMPLETO | ✅ COMPLETO |

---

## 🎨 Interface do Utilizador

### Exemplo de Fluxo: Criar Tarefa
```
Utilizador: /nova_tarefa
Bot: 📝 Vamos criar uma nova tarefa!
     Por favor, envia o título da tarefa:

Utilizador: Reunião com cliente
Bot: ✅ Título: "Reunião com cliente"
     Agora envia a descrição (ou /skip):

Utilizador: Discutir proposta de projeto
Bot: Escolhe a prioridade:
     [🔴 Alta] [🟡 Média] [🟢 Baixa]

Utilizador: [clica 🔴 Alta]
Bot: Envia a categoria/tag (ou /skip):

Utilizador: Trabalho
Bot: Envia a data de vencimento (DD/MM/AAAA HH:MM ou /skip):

Utilizador: 20/01/2025 14:00
Bot: ✅ Tarefa criada com sucesso!
     
     📋 Reunião com cliente
     📝 Discutir proposta de projeto
     🔴 Prioridade: Alta
     🏷️ Categoria: Trabalho
     📅 Vencimento: 20/01/2025 14:00
     
     Queres adicionar ao Google Calendar?
     [✅ Sim] [❌ Não]

Utilizador: [clica ✅ Sim]
Bot: 📅 Clica aqui para adicionar ao Google Calendar:
     [🔗 Adicionar ao Calendar]
```

---

## 🔒 Segurança

- ✅ Bot token armazenado em variável de ambiente
- ✅ Base de dados SQLite local (isolada por utilizador)
- ✅ Sem OAuth (links públicos do Google Calendar)
- ✅ Sem armazenamento de dados sensíveis

---

## 📈 Próximas Melhorias (Futuro)

### Funcionalidades Adicionais
- [ ] Notificações de tarefas próximas do vencimento
- [ ] Tarefas recorrentes (diárias, semanais, mensais)
- [ ] Subtarefas
- [ ] Anexos (fotos, documentos)
- [ ] Partilha de tarefas com outros utilizadores
- [ ] Exportar tarefas (CSV, PDF)

### Integrações
- [ ] Google Tasks API (sincronização bidirecional)
- [ ] Trello
- [ ] Notion
- [ ] Todoist

### UI/UX
- [ ] Inline keyboard para edição rápida
- [ ] Drag & drop de prioridades
- [ ] Temas personalizados
- [ ] Emojis personalizados por categoria

---

## 📝 Notas de Desenvolvimento

### Decisões Técnicas
1. **SQLite vs PostgreSQL:** Escolhido SQLite pela simplicidade (uso pessoal)
2. **Links vs OAuth:** Links diretos para evitar complexidade
3. **Async/await:** python-telegram-bot v20+ requer async
4. **Modular:** Separação em database.py, tasks.py, utils.py para manutenção

### Desafios Resolvidos
- ✅ Conversação multi-etapa para criar tarefas
- ✅ Gestão de estado (ConversationHandler)
- ✅ Formatação de datas (DD/MM/AAAA HH:MM)
- ✅ URL encoding para Google Calendar
- ✅ Callback queries para botões interativos

---

## 🎉 Resultado Final

**Bot totalmente funcional e pronto para produção!**

### Checklist Final
- ✅ Código completo e testado
- ✅ Base de dados configurada
- ✅ Todos os comandos implementados
- ✅ Google Calendar integrado
- ✅ Repositório GitHub criado
- ✅ Guia de deploy preparado
- ✅ Documentação completa
- ⏳ Deploy no Railway (próximo passo)

---

**Desenvolvido com ❤️ por Manus AI**
**Data:** Janeiro 2025
