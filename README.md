# WhatsApp Transport Bot

Automacao em Python para gerenciar grupos de transporte universitario no WhatsApp Web.

## O que este projeto faz

- Abre grupos e ativa envio de mensagens (scripts de abertura)
- Envia avisos antes do fechamento das listas
- Fecha grupos, extrai listas e gera quantitativos com IA
- Envia resumo para o grupo de coordenacao

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

## Requisitos

- Python 3.10+
- Google Chrome instalado
- Conta WhatsApp ja logada no Chrome
- Chave da API Google AI (Gemini)

## Instalacao

```bash
python -m venv .venv
.venv\Scripts\activate
pip install selenium webdriver-manager google-genai
```

## Configuracao da chave da IA

1. Copie `api_key_config.example.py` para `api_key_config.py`.
2. Defina sua chave no arquivo criado:

```python
GOOGLE_API_KEY = "sua_chave_aqui"
```

## Execucao

Exemplos:

```bash
python abrir_grupos_07h.py
python aviso_matutino_1930.py
python fechar_noturno_12h.py
```

## Observacoes importantes

- Os scripts usam um perfil Chrome local para manter a sessao do WhatsApp.
- O arquivo de log `whatsapp_automacao.log` e gerado localmente e ignorado no Git.
- A pasta `Teste/` esta ignorada no Git para nao subir scripts de validacao local.

## Seguranca

- Nao versione sua chave da API.
- O arquivo `api_key_config.py` esta no `.gitignore` e nao sera enviado ao GitHub.

## Licenca

Uso interno e privado.
