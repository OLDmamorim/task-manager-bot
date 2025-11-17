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

- [x] AttributeError: 'NoneType' object has no attribute 'id'
- [x] Corrigir acesso a user_id em callbacks (usar query.from_user.id)
- [ ] Testar novamente


## Erro is_overdue

- [x] AttributeError: 'dict' object has no attribute 'date'
- [x] Corrigir função get_status_emoji() em utils.py
- [ ] Testar comandos /tarefas, /hoje, /tarefas_ativas


## Erro NameError

- [ ] NameError: name 'is_overdue' is not defined
- [ ] Reorganizar ordem das funções em utils.py
- [ ] Testar novamente
