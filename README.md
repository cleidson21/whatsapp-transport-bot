# WhatsApp Transport Bot

Automacao em Python para gerenciar grupos de transporte universitario no WhatsApp Web.

Este projeto foi pensado para operacao diaria: abrir grupos nos horarios certos, enviar avisos, fechar listas e consolidar quantitativos para a coordenacao.

## O que este projeto faz

- Abre grupos e ativa envio de mensagens (scripts de abertura)
- Envia avisos antes do fechamento das listas
- Fecha grupos e solicita listas ao grupo de operação (sem coleta automática)
- Envia solicitação ao grupo de operação em vez de consolidar automaticamente

## Funcionalidades principais

- Abertura automatica de grupos por turno (manha, tarde, noite e sabado)
- Fechamento automatizado de permissao de envio nos grupos
- Captura da ultima lista relevante no chat (com tentativa de expandir "Ler mais")
 - Não captura listas nem processa dados com IA; apenas fecha grupos e envia solicitações
- Normalizacao de formato da mensagem para evitar marcadores duplicados no WhatsApp
- Logs de execucao em arquivo e no console para auditoria
- Reaproveitamento de sessao do WhatsApp Web via perfil fixo do Chrome

## Novidades recentes

- Bot agora opera em modo seguro: não coleta mensagens nem usa IA; envia solicitações simples ao grupo `Operação Transporte Universitário`.
- Envio de aviso de fechamento mesmo quando o grupo já está fechado.
- Seletor de caixa de mensagem mais robusto para envio de mensagens no WhatsApp Web.

## Estrutura principal

- `abrir_grupos_07h.py`
- `abrir_grupos_17h.py`
- `abrir_grupo_Sabado.py`
- `aviso_matutino_1930.py`
- `aviso_vespertino_0930.py`
- `aviso_noturno_1130.py`
- `fechar_matutino_20h.py`
- `fechar_vespertino_10h.py`
- `fechar_noturno_12h.py`
- `fechar_sabado_20h.py`
- `warmup_whatsapp.py`
 
## Fluxo operacional (resumo)

1. Scripts de abertura habilitam envio de mensagens nos grupos.
2. Scripts de aviso notificam o fechamento com antecedencia.
3. Scripts de fechamento bloqueiam envio e solicitam a lista ao grupo de operação.
4. A solicitação é enviada ao grupo `Operação Transporte Universitário`.

## Requisitos

- Python 3.10+
- Google Chrome instalado
- Conta WhatsApp ja logada no Chrome
- (Sem necessidade de chave de IA)

## Instalacao

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Dependencias usadas:

- `selenium`
- `webdriver-manager`

## Execucao

Exemplos:

```bash
python abrir_grupos_07h.py
python aviso_matutino_1930.py
python fechar_noturno_12h.py
```

Sugestao de ordem em ambiente real:

1. `warmup_whatsapp.py`
2. Script de abertura do turno
3. Script de aviso do turno
4. Script de fechamento do turno

## Agendador de Tarefas (Windows)

Para cada tarefa, configure:

- Programa/script: caminho do `python.exe`
- Iniciar em: pasta do projeto
- Argumentos: nome do script (ex: `fechar_noturno_12h.py`)

Isso evita erro de caminho relativo e garante que o perfil local do Chrome seja usado corretamente.

## Observacoes importantes

- Os scripts usam um perfil Chrome local para manter a sessao do WhatsApp.
- O arquivo de log `whatsapp_automacao.log` e gerado localmente e ignorado no Git.
- A pasta `Teste/` esta ignorada no Git para nao subir scripts de validacao local.
- O primeiro login no WhatsApp Web deve ser feito manualmente nesse perfil.

## Seguranca

- Nao versione sua chave da API.
- O arquivo `api_key_config.py` esta no `.gitignore` e nao sera enviado ao GitHub.
- Revogue e gere nova chave imediatamente se ela for exposta por engano.

## Licenca

Uso interno e privado.
