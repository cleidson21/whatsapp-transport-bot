# WhatsApp Transport Bot

Automacao em Python para gerenciar grupos de transporte universitario no WhatsApp Web.

Este projeto foi pensado para operacao diaria: abrir grupos nos horarios certos, enviar avisos, fechar listas e consolidar quantitativos para a coordenacao.

## O que este projeto faz

- Abre grupos e ativa envio de mensagens (scripts de abertura)
- Envia avisos antes do fechamento das listas
- Fecha grupos, extrai listas e gera quantitativos com IA
- Envia resumo para o grupo de coordenacao

## Funcionalidades principais

- Abertura automatica de grupos por turno (manha, tarde, noite e sabado)
- Fechamento automatizado de permissao de envio nos grupos
- Captura da ultima lista relevante no chat (com tentativa de expandir "Ler mais")
- Processamento via IA para consolidar quantitativos por rota/turno
- Normalizacao de formato da mensagem para evitar marcadores duplicados no WhatsApp
- Logs de execucao em arquivo e no console para auditoria
- Reaproveitamento de sessao do WhatsApp Web via perfil fixo do Chrome

## Novidades recentes

- Fallback automatico de modelos Gemini para reduzir falhas por indisponibilidade momentanea
- Ordem padrao de fallback da IA: `gemini-2.5-flash` -> `gemini-3.1-flash` -> `gemini-3.1-flash-lite` -> `gemini-2.5-pro`
- Retry com backoff exponencial para erros temporarios (`503`, `429`, `UNAVAILABLE`)
- Logs detalhados da etapa da IA (inicio, tentativas por modelo, troca de modelo e resultado)
- Envio de aviso de fechamento mesmo quando o grupo ja esta fechado
- Seletor de caixa de mensagem mais robusto para envio de relatorio no WhatsApp Web

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
- `ia_fallback_helper.py`
- `warmup_whatsapp.py`

## Fluxo operacional (resumo)

1. Scripts de abertura habilitam envio de mensagens nos grupos.
2. Scripts de aviso notificam o fechamento com antecedencia.
3. Scripts de fechamento bloqueiam envio, extraem listas e geram quantitativos com IA.
4. Resultado final e enviado ao grupo de coordenacao.

## Requisitos

- Python 3.10+
- Google Chrome instalado
- Conta WhatsApp ja logada no Chrome
- Chave da API Google AI (Gemini)

## Instalacao

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Dependencias usadas:

- `selenium`
- `webdriver-manager`
- `google-genai`

## Configuracao da chave da IA

1. Copie `api_key_config.example.py` para `api_key_config.py`.
2. Defina sua chave no arquivo criado:

```python
GOOGLE_API_KEY = "sua_chave_aqui"
```

Observacao:

- `api_key_config.py` esta no `.gitignore` e nao sobe para o GitHub.

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
