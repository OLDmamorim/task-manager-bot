# Task Manager Bot - TODO

## Melhorias Solicitadas

- [x] Adicionar dependência python-telegram-bot-calendar ao requirements.txt
- [x] Implementar calendário visual para seleção de data (em vez de texto)
- [x] Remover pedido de hora (apenas data)
- [x] Criar novo comando /tarefas_ativas
- [x] Adicionar checkboxes interativos para marcar tarefas como concluídas
- [ ] Testar funcionalidades localmente
- [x] Commit e push para GitHub
- [ ] Verificar deploy no Railway


## Problema Reportado

- [x] Apenas /stats funciona, outros comandos não respondem (CORRIGIDO)
- [x] Verificar logs do Railway
- [x] Identificar erro com python-telegram-bot-calendar (ModuleNotFoundError)
- [x] Corrigir erro (criado calendar_utils.py personalizado)
- [ ] Testar todos os comandos


## Novo Erro

- [ ] AttributeError: 'NoneType' object has no attribute 'id'
- [ ] Corrigir acesso a user_id em callbacks
- [ ] Testar novamente
