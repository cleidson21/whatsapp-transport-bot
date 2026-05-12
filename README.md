# WhatsApp Transport Bot

<<<<<<< HEAD
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

=======
Automacao em Python para abrir, avisar e fechar grupos de transporte universitario via Evolution API.

O projeto foi organizado para executar tarefas pontuais por horario, com logs locais e configuracao simples para ambiente de teste ou producao.

## Visao geral

- `whatsapp-transport-bot-main/` concentra os scripts de automacao.
- `servidor-whatsapp/` concentra a pilha de infraestrutura local para a Evolution API.
- `servidor-whatsapp/docker-compose.yml` sobe a Evolution API, Redis, PostgreSQL e o painel web.
- Os scripts usam `requests` para consultar grupos e alterar o status de permissao de envio.

## Estrutura principal

- `whatsapp-transport-bot-main/abrir_grupos_07h.py`
- `whatsapp-transport-bot-main/abrir_grupos_17h.py`
- `whatsapp-transport-bot-main/abrir_grupo_Sabado.py`
- `whatsapp-transport-bot-main/aviso_matutino_1930.py`
- `whatsapp-transport-bot-main/aviso_vespertino_0930.py`
- `whatsapp-transport-bot-main/aviso_noturno_1130.py`
- `whatsapp-transport-bot-main/fechar_matutino_20h.py`
- `whatsapp-transport-bot-main/fechar_vespertino_10h.py`
- `whatsapp-transport-bot-main/fechar_noturno_12h.py`
- `whatsapp-transport-bot-main/fechar_sabado_20h.py`
- `whatsapp-transport-bot-main/humanizer.py`

> Observacao: o antigo fluxo de `warmup` nao faz mais parte da operacao atual e foi removido da estrutura ativa do projeto.

## Dependencias

- Python 3.10 ou superior
- `requests`
- Evolution API em execucao local em `http://localhost:8080`

## Instalacao

Crie o ambiente virtual e instale as dependencias:

>>>>>>> 5763e32 (Atualiza estrutura e documentacao do projeto)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
 # WhatsApp Transport Bot

Automacao em Python para abrir, avisar e fechar grupos de transporte universitario via Evolution API.

O projeto foi organizado para executar tarefas pontuais por horario, com logs locais e configuracao simples para ambiente de teste ou producao.

## Visao geral

- `whatsapp-transport-bot-main/` concentra os scripts de automacao.
- `servidor-whatsapp/` concentra a pilha de infraestrutura local para a Evolution API.
- `servidor-whatsapp/docker-compose.yml` sobe a Evolution API, Redis, PostgreSQL e o painel web.
- Os scripts usam `requests` para consultar grupos e alterar o status de permissao de envio.

## Estrutura principal

- `whatsapp-transport-bot-main/abrir_grupos_07h.py`
- `whatsapp-transport-bot-main/abrir_grupos_17h.py`
- `whatsapp-transport-bot-main/abrir_grupo_Sabado.py`
- `whatsapp-transport-bot-main/aviso_matutino_1930.py`
- `whatsapp-transport-bot-main/aviso_vespertino_0930.py`
- `whatsapp-transport-bot-main/aviso_noturno_1130.py`
- `whatsapp-transport-bot-main/fechar_matutino_20h.py`
- `whatsapp-transport-bot-main/fechar_vespertino_10h.py`
- `whatsapp-transport-bot-main/fechar_noturno_12h.py`
- `whatsapp-transport-bot-main/fechar_sabado_20h.py`
- `whatsapp-transport-bot-main/humanizer.py`

> Observacao: o antigo fluxo de `warmup` nao faz mais parte da operacao atual e foi removido da estrutura ativa do projeto.

## Dependencias

- Python 3.10 ou superior
- `requests`
- Evolution API em execucao local em `http://localhost:8080`

## Instalacao

Crie o ambiente virtual e instale as dependencias:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuracao

Os scripts principais da pasta `whatsapp-transport-bot-main/` podem ler as variaveis abaixo. Se elas nao forem definidas, usam valores padrao para ambiente local.

- `WHATSAPP_API_URL`: endereco da Evolution API
- `WHATSAPP_API_KEY`: chave de acesso da API
- `WHATSAPP_INSTANCE`: nome da instancia
- `WHATSAPP_GROUPS`: lista de grupos separada por ponto e virgula
- `WHATSAPP_COORDINATION_GROUP`: nome do grupo de coordenação usado nos scripts de fechamento

Exemplo no PowerShell:

```powershell
$env:WHATSAPP_API_URL = "http://localhost:8080"
$env:WHATSAPP_API_KEY = "SUA_CHAVE_AQUI"
$env:WHATSAPP_INSTANCE = "sec-educ-berimbau"
$env:WHATSAPP_GROUPS = "Transporte UEFS Sábado 2026"
python .\whatsapp-transport-bot-main\abrir_grupo_Sabado.py
```

## Execucao do servidor

Para subir a pilha da Evolution API:

```bash
cd servidor-whatsapp
docker-compose up -d
```

## Execucao dos scripts

Exemplos:

```bash
python whatsapp-transport-bot-main/abrir_grupos_07h.py
python whatsapp-transport-bot-main/aviso_matutino_1930.py
python whatsapp-transport-bot-main/fechar_noturno_12h.py
```

## Logs

Os scripts registram a execucao em arquivos `.log` no proprio diretorio do projeto. Isso facilita auditoria e depuracao sem depender do console.

## Observacoes de operacao

- Os scripts de abertura usam a Evolution API para localizar o JID do grupo pelo nome.
- Os scripts de aviso e fechamento seguem o mesmo padrao de consulta e atualizacao de status.
- O helper `humanizer.py` fornece pausas aleatorias para reduzir padroes repetitivos de execucao.

## Seguranca

- Nao commite chaves reais de API.
- Prefira variaveis de ambiente para credenciais e configuracoes de ambiente.
- Se a chave estiver exposta em qualquer copia do projeto, gere uma nova imediatamente.

## Licenca

Uso interno e privado.
- Se a chave estiver exposta em qualquer copia do projeto, gere uma nova imediatamente.
