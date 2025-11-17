# 🔍 Diagnóstico Completo - Task Manager Bot

## 📋 Resumo Executivo

Foram identificados **2 problemas críticos** que impedem o funcionamento correto do bot:

1. **Múltiplas instâncias do bot em execução** (Conflito de polling)
2. **Erro de parsing de Markdown** (Underscores não escapados)

---

## 🚨 Problema 1: Conflito de Instâncias

### Descrição
```
telegram.error.Conflict: Conflict: terminated by other getUpdates request; 
make sure that only one bot instance is running
```

### Causa Raiz
O Telegram Bot API não permite que múltiplas instâncias do mesmo bot façam polling (`getUpdates`) simultaneamente. Isto acontece quando:

- O bot está a correr em múltiplos servidores/containers ao mesmo tempo
- Uma instância anterior não foi terminada corretamente
- O Railway.app está a fazer restart automático e cria sobreposição de instâncias

### Impacto
- O bot não consegue receber mensagens dos utilizadores
- Falha intermitente na comunicação
- Comportamento imprevisível

### Solução Recomendada

**Opção 1: Usar Webhooks em vez de Polling** (Recomendado para produção)
```python
# Em vez de:
app.run_polling(allowed_updates=Update.ALL_TYPES)

# Usar:
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get('PORT', 8443)),
    url_path=TOKEN,
    webhook_url=f"https://your-app.railway.app/{TOKEN}"
)
```

**Opção 2: Garantir apenas uma instância**
- No Railway.app, verificar que apenas 1 réplica está configurada
- Adicionar timeout mais longo antes de restart
- Implementar graceful shutdown

---

## 🚨 Problema 2: Erro de Parsing de Markdown

### Descrição
```
telegram.error.BadRequest: Can't parse entities: can't find end of the entity 
starting at byte offset 265
```

### Causa Raiz
No Telegram Markdown, o underscore `_` é usado para formatação itálica. Os comandos do bot contêm underscores que não estão escapados:

- `/nova_tarefa`
- `/tarefas_ativas`
- `/apagar_tarefa`

Quando o Telegram tenta fazer parse do Markdown, interpreta estes underscores como marcadores de formatação, causando erro porque não encontra o par de fecho.

### Localização do Erro
Ficheiro: `bot.py`, linha 86-102 (função `start_command`)

```python
text = f"""
👋 **Olá, {user.first_name}!**

Bem-vindo ao **Task Manager Bot**!

📋 **Comandos principais:**
/nova_tarefa - Criar tarefa          # ❌ underscore não escapado
/tarefas_ativas - Ver tarefas        # ❌ underscore não escapado
/tarefas - Ver todas as tarefas
/hoje - Tarefas de hoje
/concluir - Marcar como concluída
/apagar_tarefa - Apagar tarefa       # ❌ underscore não escapado
/stats - Estatísticas

Digite /help para ver todos os comandos!
"""
await update.message.reply_text(text, parse_mode='Markdown')
```

### Análise Técnica
- **Byte offset 265**: Corresponde à zona onde aparece `/apagar_tarefa`
- **Underscores encontrados**: 3 (nas posições 87, 118, 252)
- **Problema**: Markdown interpreta `_tarefa` como início de itálico sem fecho

### Soluções Disponíveis

#### ✅ Solução 1: Usar HTML em vez de Markdown (MAIS SIMPLES)
```python
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
await update.message.reply_text(text, parse_mode='HTML')
```

#### ✅ Solução 2: Escapar underscores no Markdown
```python
text = f"""
👋 **Olá, {user.first_name}!**

Bem-vindo ao **Task Manager Bot**!

📋 **Comandos principais:**
/nova\\_tarefa - Criar tarefa
/tarefas\\_ativas - Ver tarefas com checkboxes
/tarefas - Ver todas as tarefas
/hoje - Tarefas de hoje
/concluir - Marcar como concluída
/apagar\\_tarefa - Apagar tarefa
/stats - Estatísticas

Digite /help para ver todos os comandos!
"""
await update.message.reply_text(text, parse_mode='Markdown')
```

#### ✅ Solução 3: Remover formatação
```python
text = f"""
👋 Olá, {user.first_name}!

Bem-vindo ao Task Manager Bot!

📋 Comandos principais:
/nova_tarefa - Criar tarefa
/tarefas_ativas - Ver tarefas com checkboxes
/tarefas - Ver todas as tarefas
/hoje - Tarefas de hoje
/concluir - Marcar como concluída
/apagar_tarefa - Apagar tarefa
/stats - Estatísticas

Digite /help para ver todos os comandos!
"""
await update.message.reply_text(text)  # Sem parse_mode
```

---

## 🔧 Outros Problemas Identificados

### 3. Comando /help também tem o mesmo problema
Ficheiro: `bot.py`, linha 105-124

O comando `/help` usa Markdown e também contém underscores não escapados. Precisa da mesma correção.

### 4. Outras mensagens com Markdown
Verificar todas as mensagens que usam `parse_mode='Markdown'` no código:
- Linha 136: `/nova_tarefa`
- Linha 155: `/tarefas`
- Linha 184: `/tarefas_ativas`
- Linha 214: `/hoje`
- Linha 241: `/concluir`
- Linha 269: `/apagar_tarefa`
- Linha 292: `/stats`

**Nota**: A maioria destas não tem underscores no texto, mas é boa prática uniformizar o `parse_mode`.

---

## 📊 Configuração do Deployment

### Railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python bot.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Problema**: `restartPolicyMaxRetries: 10` pode causar múltiplas instâncias se o bot falhar repetidamente.

**Sugestão**: 
- Reduzir para 3 retries
- Adicionar delay entre restarts
- Considerar usar webhooks

---

## ✅ Plano de Ação Prioritário

### Prioridade ALTA (Resolver imediatamente)

1. **Corrigir erro de Markdown no comando /start**
   - Alterar `parse_mode='Markdown'` para `parse_mode='HTML'`
   - Substituir `**texto**` por `<b>texto</b>`
   - Ficheiro: `bot.py`, linha 102

2. **Corrigir erro de Markdown no comando /help**
   - Aplicar mesma correção
   - Ficheiro: `bot.py`, linha 124

3. **Resolver conflito de instâncias**
   - Verificar no Railway.app se há múltiplas instâncias
   - Parar todas as instâncias antigas
   - Garantir que apenas 1 réplica está configurada

### Prioridade MÉDIA (Melhorias)

4. **Uniformizar parse_mode em todo o código**
   - Decidir entre HTML ou Markdown
   - Aplicar consistentemente
   - Criar função auxiliar para formatação

5. **Migrar para Webhooks**
   - Melhor para produção
   - Evita conflitos de polling
   - Mais eficiente

### Prioridade BAIXA (Otimizações)

6. **Adicionar error handlers**
   - O código mostra: "No error handlers are registered"
   - Implementar tratamento de erros global

7. **Adicionar logging melhorado**
   - Facilitar debug futuro
   - Monitorizar estado do bot

---

## 🧪 Como Testar as Correções

1. Fazer as alterações no código
2. Fazer commit e push para o GitHub
3. Aguardar deploy no Railway.app
4. Verificar logs para confirmar que não há mais erros
5. Testar comando `/start` no Telegram
6. Testar comando `/help` no Telegram
7. Verificar que não há mais conflitos de polling

---

## 📝 Notas Adicionais

- O bot usa SQLite como base de dados (ficheiro `database.py`)
- Não há ficheiro `.env` no repositório (normal, deve estar nas variáveis de ambiente do Railway)
- O token do bot está exposto nos logs (considerar rodar o token por segurança)
- O projeto está bem estruturado, apenas precisa destas correções pontuais

---

**Data do diagnóstico**: 2025-11-17  
**Versão analisada**: Commit mais recente do repositório
