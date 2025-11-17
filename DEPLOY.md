# 🚀 Guia de Deploy no Railway

## Pré-requisitos
- Conta no [Railway](https://railway.app/)
- Bot Token do Telegram: `8428607015:AAG-Ag9Rhj-PyCqoBHA0k0GhjsPRoNWrUpw`

## Passo a Passo

### 1. Criar Novo Projeto no Railway
1. Acesse [railway.app](https://railway.app/)
2. Clique em **"New Project"**
3. Selecione **"Deploy from GitHub repo"**

### 2. Conectar o Repositório
1. Autorize o Railway a aceder ao GitHub (se ainda não fez)
2. Selecione o repositório: **`OLDmamorim/task-manager-bot`**
3. Clique em **"Deploy Now"**

### 3. Configurar Variáveis de Ambiente
1. No dashboard do projeto, clique em **"Variables"**
2. Adicione a seguinte variável:
   ```
   BOT_TOKEN=8428607015:AAG-Ag9Rhj-PyCqoBHA0k0GhjsPRoNWrUpw
   ```
3. Clique em **"Add"** ou pressione Enter

### 4. Deploy Automático
O Railway vai:
- ✅ Instalar as dependências do `requirements.txt`
- ✅ Criar a base de dados SQLite
- ✅ Iniciar o bot automaticamente
- ✅ Manter o bot sempre ativo

### 5. Verificar o Deploy
1. Vá para a aba **"Deployments"**
2. Aguarde até ver **"Success"** (pode demorar 2-3 minutos)
3. Verifique os logs clicando no deployment

### 6. Testar o Bot
1. Abra o Telegram
2. Procure pelo bot: **@YourBotName** (o nome que definiu no BotFather)
3. Envie `/start`
4. Deve receber a mensagem de boas-vindas! 🎉

## Comandos Disponíveis

### Gestão de Tarefas
- `/start` - Mensagem de boas-vindas e menu principal
- `/nova_tarefa` - Criar nova tarefa
- `/tarefas` - Listar todas as tarefas
- `/hoje` - Ver tarefas de hoje
- `/concluir` - Marcar tarefa como concluída
- `/editar` - Editar uma tarefa existente
- `/apagar_tarefa` - Apagar uma tarefa

### Organização
- `/categorias` - Gerir categorias
- `/stats` - Ver estatísticas de produtividade

## Funcionalidades

### ✅ Criação de Tarefas
- Título e descrição
- Prioridade (Alta/Média/Baixa)
- Categoria/tag
- Data de vencimento
- **Integração com Google Calendar** (link direto)

### 📊 Visualização
- Lista de todas as tarefas
- Filtro por pendentes/concluídas
- Tarefas de hoje
- Estatísticas completas

### 🔄 Gestão
- Marcar como concluída
- Editar detalhes
- Apagar tarefas
- Gerir categorias

### 📅 Google Calendar
Quando cria uma tarefa com data/hora, o bot pergunta se quer adicionar ao Google Calendar.
Se responder "Sim", recebe um link clicável que abre o Google Calendar com o evento pré-preenchido!

## Troubleshooting

### Bot não responde
1. Verifique se o deploy foi bem-sucedido
2. Confirme que a variável `BOT_TOKEN` está correta
3. Verifique os logs no Railway

### Erro de base de dados
- O SQLite é criado automaticamente na primeira execução
- Se houver problemas, faça redeploy

### Bot offline
- O Railway mantém o bot sempre ativo
- Se parar, reinicia automaticamente

## Manutenção

### Ver Logs
1. No Railway, clique no projeto
2. Vá para **"Deployments"**
3. Clique no deployment ativo
4. Veja os logs em tempo real

### Atualizar o Bot
1. Faça push das alterações para o GitHub
2. O Railway faz redeploy automaticamente
3. Aguarde 2-3 minutos

### Fazer Rollback
1. Vá para **"Deployments"**
2. Encontre o deployment anterior
3. Clique em **"Redeploy"**

## Custos
- Railway oferece **$5 de crédito grátis por mês**
- Este bot consome muito pouco (< $1/mês)
- Suficiente para uso pessoal

## Suporte
Se tiver problemas:
1. Verifique os logs no Railway
2. Confirme que todas as variáveis estão corretas
3. Teste os comandos no Telegram

---

**Bot criado com ❤️ usando python-telegram-bot v20+**
