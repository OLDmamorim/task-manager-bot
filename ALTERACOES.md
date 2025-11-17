# 🔧 Resumo das Alterações Aplicadas

## Ficheiro: bot_CORRIGIDO.py

### Alterações Principais

#### 1. Mudança de Markdown para HTML
**Razão**: Evitar conflitos com underscores nos nomes dos comandos

**Antes:**
```python
parse_mode='Markdown'
**texto em negrito**
`código`
```

**Depois:**
```python
parse_mode='HTML'
<b>texto em negrito</b>
<code>código</code>
```

#### 2. Funções Alteradas

##### start_command (linha 87-103)
- ✅ Alterado `parse_mode='Markdown'` para `parse_mode='HTML'`
- ✅ Alterado `**texto**` para `<b>texto</b>`

##### help_command (linha 106-127)
- ✅ Alterado `parse_mode='Markdown'` para `parse_mode='HTML'`
- ✅ Alterado `**texto**` para `<b>texto</b>`

##### nova_tarefa_command (linha 135)
- ✅ Alterado para HTML

##### tarefas_command (linha 155)
- ✅ Alterado para HTML

##### tarefas_ativas_command (linha 184)
- ✅ Alterado para HTML

##### hoje_command (linha 214)
- ✅ Alterado para HTML

##### concluir_command (linha 241)
- ✅ Alterado para HTML

##### apagar_tarefa_command (linha 269)
- ✅ Alterado para HTML

##### stats_command (linha 292)
- ✅ Alterado para HTML

##### callback_handler
- ✅ Todas as mensagens alteradas para HTML

##### format_task_text (linha 51)
- ✅ Alterado `**{title}**` para `<b>{title}</b>`
- ✅ Alterado `` `{task['id']}` `` para `<code>{task['id']}</code>`

#### 3. Adicionado Error Handler
```python
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler global para erros"""
    logger.error(f"Erro ao processar update: {context.error}")
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Ocorreu um erro ao processar o seu pedido. Por favor, tente novamente."
            )
    except:
        pass
```

Registado no main():
```python
app.add_error_handler(error_handler)
```

---

## Como Aplicar as Correções

### Opção 1: Substituir o ficheiro completo
```bash
# Fazer backup do original
cp bot.py bot_ORIGINAL.py

# Substituir pelo corrigido
cp bot_CORRIGIDO.py bot.py

# Commit e push
git add bot.py
git commit -m "fix: corrigir erro de parsing Markdown e adicionar error handler"
git push
```

### Opção 2: Aplicar apenas as alterações críticas
Se preferires fazer alterações manuais, as mudanças mínimas são:

1. **Linha 102** (start_command):
   - Mudar `parse_mode='Markdown'` para `parse_mode='HTML'`
   - Mudar `**` para `<b>` e `</b>`

2. **Linha 124** (help_command):
   - Mudar `parse_mode='Markdown'` para `parse_mode='HTML'`
   - Mudar `**` para `<b>` e `</b>`

---

## Resolver Conflito de Instâncias

### No Railway.app:

1. Aceder ao dashboard do projeto
2. Ir a "Settings" → "Deploy"
3. Verificar "Replicas": deve estar em **1**
4. Em "Restart Policy", considerar reduzir retries de 10 para 3
5. Parar todas as deployments antigas
6. Fazer novo deploy com o código corrigido

### Alternativa: Usar Webhooks

Criar ficheiro `bot_webhook.py`:
```python
# No final do main(), substituir:
# app.run_polling(allowed_updates=Update.ALL_TYPES)

# Por:
PORT = int(os.environ.get('PORT', 8443))
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path=TOKEN,
    webhook_url=f"{os.environ.get('RAILWAY_PUBLIC_DOMAIN')}/{TOKEN}"
)
```

No Railway.app, adicionar variável de ambiente:
- `RAILWAY_PUBLIC_DOMAIN`: URL público do teu serviço

---

## Testar as Correções

1. ✅ Verificar logs - não deve haver mais erros de parsing
2. ✅ Testar `/start` - deve mostrar mensagem formatada
3. ✅ Testar `/help` - deve funcionar sem erros
4. ✅ Testar criação de tarefa
5. ✅ Verificar que não há conflitos de polling

---

## Checklist Final

- [ ] Código corrigido aplicado
- [ ] Commit e push feitos
- [ ] Deploy no Railway concluído
- [ ] Logs verificados (sem erros)
- [ ] Comando /start testado
- [ ] Comando /help testado
- [ ] Apenas 1 instância a correr
- [ ] Bot a responder normalmente

---

**Nota**: Estas alterações resolvem os 2 problemas críticos identificados nos logs.
