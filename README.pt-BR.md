# WhatsApp Transport Bot - Hub Centralizado de Gestão de Frotas e Listas Universitárias

<p align="center">
  <a href="README.md">English</a> • <a href="README.pt-BR.md"><b>Português</b></a>
</p>

Sistema automatizado de código aberto para moderação, abertura, avisos e fechamento de listas em grupos de transporte estudantil universitário no WhatsApp. Utiliza a **Evolution API**, conteinerização unificada em **Docker Compose**, agendamento dinâmico via **`config.json`** e rotinas avançadas de proteção anti-ban.

---

## 🚀 Visão Geral

Este projeto oferece uma solução centralizada, modular e genérica para associações de estudantes, prefeituras, cooperativas e comissões de transporte universitário que precisam gerenciar múltiplos grupos de WhatsApp diariamente.

Elimina rotinas manuais e scripts dispersos ao orquestrar todo o ciclo de operação dos grupos:
1. **Abertura programada dos grupos** para envio de mensagens pelos passageiros.
2. **Avisos prévios parametrizáveis** alertando sobre o encerramento iminente das listas.
3. **Fechamento e trancamento automático** dos grupos (restringindo mensagens a administradores).
4. **Notificação à coordenação geral** solicitando o fechamento ou resumo das listas.

---

## ⚡ Guia Rápido de Instalação

### Pré-requisitos
- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/) instalados.

### 1. Clonar o repositório e preparar as configurações
```bash
git clone https://github.com/cleidson21/whatsapp-transport-bot.git
cd whatsapp-transport-bot
cp .env.example .env
cp config.example.json config.json
```

### 2. Subir a stack completa
```bash
docker compose up -d --build
```

### 3. Conectar a instância do WhatsApp
1. Acesse o painel do **Evolution Manager** em: [http://localhost:3000](http://localhost:3000).
2. Configure a URL da API como `http://localhost:8080` e informe a sua `AUTHENTICATION_API_KEY` definida no `.env`.
3. Crie a instância com o nome configurado na variável `WHATSAPP_INSTANCE` (padrão: `transporte-hub`).
4. Leia o QR Code no seu WhatsApp (Aparelhos Conectados > Conectar um aparelho).

### 4. Monitorar a operação
```bash
docker compose logs -f hub_bot
```

Para pausar os serviços:
```bash
docker compose down
```

---

## 📁 Estrutura do Repositório

```text
├── app/
│   ├── __init__.py
│   ├── api_client.py       # Integração HTTP com a Evolution API
│   ├── humanizer.py        # Algoritmos de pausas randômicas e jitter humano
│   └── main.py             # Orquestrador central e agendador de turnos
├── config.example.json     # Template genérico de turnos, horários e grupos
├── docker-compose.yml      # Orquestração (PostgreSQL, Redis, Evolution API, Manager e Bot)
├── Dockerfile              # Imagem do container do bot
├── requirements.txt        # Dependências Python (requests, schedule)
├── .env.example            # Modelo de variáveis de ambiente
├── README.md               # Documentação principal em Inglês
└── README.pt-BR.md         # Documentação em Português
```

---

## ⚙️ Customização de Turnos e Rotas (`config.json`)

Toda a grade de horários, turnos e grupos é definida no arquivo `config.json`. Você pode criar quantos turnos forem necessários (ex: matutino, vespertino, noturno, fins de semana):

```json
{
  "grupo_coordenacao": "Coordination Dispatch Group",
  "turnos": {
    "matutino": {
      "horarios": {
        "abrir": "07:00",
        "avisar": "19:30",
        "fechar": "20:00"
      },
      "grupos": [
        "Transport Morning - Campus 1",
        "Transport Morning - Campus 2"
      ]
    },
    "vespertino": {
      "horarios": {
        "abrir": "13:00",
        "avisar": "09:30",
        "fechar": "10:00"
      },
      "grupos": [
        "Transport Afternoon - Route A"
      ]
    },
    "noturno": {
      "horarios": {
        "abrir": "17:00",
        "avisar": "11:30",
        "fechar": "12:00"
      },
      "grupos": [
        "Transport Evening - University 1",
        "Transport Evening - University 2"
      ]
    },
    "sabado": {
      "horarios": {
        "abrir": "17:00",
        "avisar": "11:30",
        "fechar": "12:00"
      },
      "grupos": [
        "Transport Saturday - Route 1"
      ]
    }
  }
}
```

- **`grupo_coordenacao`**: Nome exato do grupo no WhatsApp onde os resumos ou ordens de fechamento serão notificados.
- **`horarios`**:
  - `abrir`: Horário (HH:MM) em que as permissões do grupo serão alteradas para permitir envio de mensagens por todos os membros.
  - `avisar`: Horário (HH:MM) em que o aviso prévio de fechamento será enviado no grupo.
  - `fechar`: Horário (HH:MM) em que o grupo será trancado para administradores e a mensagem de encerramento enviada.
- **`grupos`**: Lista com os nomes dos grupos no WhatsApp pertencentes àquele turno.

---

## 🛡️ Proteção Anti-Ban e Heurísticas de Humanização

Para proteger os números de moderação contra bloqueios e análises heurísticas da Meta, a aplicação implementa diversas camadas de humanização:

1. **Jitter Humano Pré-Execução**:
   - As tarefas programadas não disparam no segundo exato `00`. O bot aplica um atraso aleatório (*jitter*) de alguns segundos antes de iniciar a rotina, emulando um operador humano abrindo o aplicativo.

2. **Simulação de Digitação (`presence: composing`)**:
   - Todo disparo de mensagem envia o estado `composing` (exibindo *"digitando..."* na conversa) por um intervalo randômico de 4 a 7 segundos antes do envio efetivo.

3. **Variação Dinâmica de Templates de Mensagem**:
   - Avisos e notificações de fechamento utilizam modelos textuais dinâmicos selecionados aleatoriamente. Isso impede a geração de hashes criptográficos idênticos em mensagens consecutivas para múltiplos grupos.

4. **Intervalos Realistas entre Grupos**:
   - Entre a alteração de um grupo e outro, o bot aguarda pausas randômicas de 12 a 35 segundos (`look_at_screen_pause`), simulando a navegação na interface.

5. **Pausa Operacional Pós-Fechamento**:
   - Após trancar os grupos dos estudantes, o bot aguarda de 1 a 5 minutos antes de enviar a notificação ao grupo de coordenação.

---

## 🔐 Variáveis de Ambiente (`.env`)

Copie o `.env.example` para `.env` e configure suas credenciais:

| Variável | Descrição | Exemplo |
| :--- | :--- | :--- |
| `POSTGRES_DATABASE` | Banco de dados da Evolution API | `evolution` |
| `POSTGRES_USERNAME` | Usuário do banco de dados | `evolution` |
| `POSTGRES_PASSWORD` | Senha do banco de dados | `sua_senha_postgres_aqui` |
| `AUTHENTICATION_API_KEY` | Chave de API mestra da Evolution API | `sua_chave_global_evolution_aqui` |
| `SERVER_URL` | URL de acesso à API | `http://localhost:8080` |
| `WHATSAPP_API_URL` | Endpoint da Evolution API acessível pelo bot | `http://evolution_api:8080` |
| `WHATSAPP_API_KEY` | Chave de acesso usada pelo bot | `sua_chave_evolution_aqui` |
| `WHATSAPP_INSTANCE` | Nome da instância do WhatsApp | `transporte-hub` |
| `WHATSAPP_COORDINATION_GROUP` | (Opcional) Sobrescreve o grupo de coordenação | `Coordination Dispatch Group` |

---

## 📄 Licença

Este projeto é disponibilizado sob a licença open-source [MIT](LICENSE).

