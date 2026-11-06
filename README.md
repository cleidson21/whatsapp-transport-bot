# WhatsApp Transport Bot - Hub Centralizado Dockerizado

Sistema automatizado para gerenciamento e moderação de grupos de transporte universitário no WhatsApp utilizando a **Evolution API**, arquitetura unificada em **Docker Compose** e agendamento dinâmico via **`config.json`**.

---

## 🚀 Visão Geral da Arquitetura

O projeto foi refatorado para funcionar como um **Hub Centralizado**, eliminando scripts estáticos dispersos e agendadores externos. Toda a rotina operacional (abertura de grupos, avisos prévios de fechamento e trancamento com solicitação à coordenação) é executada por um único serviço inteligente (`hub_bot`) integrado aos serviços da Evolution API.

### Componentes da Stack

- **`hub_bot`**: Aplicação Python conteinerizada que consome o `config.json`, agenda os turnos via `schedule` e executa as ações com proteção anti-ban (`humanizer`).
- **`evolution_api`**: API REST para controle e envio de mensagens no WhatsApp via instâncias Baileys.
- **`evolution_frontend`**: Painel visual de gerenciamento da Evolution API (Evolution Manager).
- **`postgres`**: Banco de dados relacional para persistência de sessões e dados da Evolution API.
- **`redis`**: Cache e fila para mensagens e instâncias da Evolution API.

---

## 📁 Estrutura do Projeto

```text
├── app/
│   ├── __init__.py
│   ├── api_client.py    # Cliente HTTP para integração com a Evolution API
│   ├── humanizer.py     # Pausas randômicas e proteção anti-ban
│   └── main.py          # Orquestrador central e agendador de turnos
├── config.json          # Configuração centralizada de turnos, grupos e horários
├── docker-compose.yml   # Orquestração de todos os serviços (Banco, API e Bot)
├── Dockerfile           # Imagem Python para execução do hub_bot
├── requirements.txt     # Dependências Python (requests, schedule)
├── .env.example         # Exemplo de variáveis de ambiente
└── README.md            # Documentação da aplicação
```

---

## ⚙️ Configuração Centralizada (`config.json`)

Todos os turnos, grupos de alunos e janelas de horário são centralizados no arquivo `config.json` na raiz do projeto:

```json
{
  "grupo_coordenacao": "Operação Transporte Universitário",
  "turnos": {
    "matutino": {
      "horarios": { "abrir": "07:00", "avisar": "19:30", "fechar": "20:00" },
      "grupos": [
        "Transporte Matutino (Centro) 2026",
        "Transporte IFBA-UNEF Matutino 2026",
        "Transporte FTC INTEGRAL 2026",
        "Transporte UEFS-UFRB 2026"
      ]
    },
    "vespertino": {
      "horarios": { "abrir": "13:00", "avisar": "09:30", "fechar": "10:00" },
      "grupos": [
        "Transporte Vespertino 2026",
        "Transporte FTC INTEGRAL 2026",
        "Transporte UEFS-UFRB 2026"
      ]
    },
    "noturno": {
      "horarios": { "abrir": "17:00", "avisar": "11:30", "fechar": "12:00" },
      "grupos": [
        "Transporte FTC Noturno 2026",
        "Transporte FAN Noturno 2026",
        "Transporte FAT Noturno 2026",
        "Transporte UNIFACS Noturno 2026",
        "Transporte IFBA-UNEF Noturno 2026",
        "Transporte UEFS Noturno 2026",
        "Transporte SENAI-PITAGORAS Noturno 2026"
      ]
    },
    "sabado": {
      "horarios": { "abrir": "07:00", "avisar": "19:30", "fechar": "20:00" },
      "grupos": [
        "Transporte UEFS Sábado 2026"
      ]
    }
  }
}
```

---

## 🔐 Variáveis de Ambiente (`.env`)

Crie o arquivo `.env` a partir do modelo `.env.example`:

```bash
cp .env.example .env
```

### Mapeamento das Variáveis:

| Variável | Descrição | Exemplo Padrão |
| :--- | :--- | :--- |
| `POSTGRES_DATABASE` | Nome do banco de dados PostgreSQL | `evolution` |
| `POSTGRES_USERNAME` | Usuário do PostgreSQL | `evolution` |
| `POSTGRES_PASSWORD` | Senha do PostgreSQL | `evolution_secret_pass` |
| `AUTHENTICATION_API_KEY` | Chave de autenticação global da Evolution API | `Transporte_Universitario_2026_Secreta` |
| `SERVER_URL` | URL pública da Evolution API | `http://localhost:8080` |
| `WHATSAPP_API_URL` | URL interna da Evolution API acessível pelo bot | `http://evolution_api:8080` |
| `WHATSAPP_API_KEY` | Chave da Evolution API utilizada pelo bot | `Transporte_Universitario_2026_Secreta` |
| `WHATSAPP_INSTANCE` | Nome da instância conectada no WhatsApp | `sec-educ-berimbau` |
| `WHATSAPP_COORDINATION_GROUP` | (Opcional) Sobrescreve o grupo de coordenação | `Operação Transporte Universitário` |

---

## 🚦 Como Iniciar a Aplicação

Com o Docker e Docker Compose instalados em seu ambiente, execute:

### 1. Subir todos os serviços com build:
```bash
docker compose up -d --build
```

### 2. Monitorar os logs do Bot:
```bash
docker compose logs -f hub_bot
```

### 3. Acessar o Painel da Evolution API:
Abra o navegador em: [http://localhost:3000](http://localhost:3000) e conecte a instância via QR Code.

### 4. Parar os serviços:
```bash
docker compose down
```

---

## 🛡️ Mecanismo Anti-Ban e Comportamento Humanizado

Para proteger os números de moderação contra bloqueios da Meta, o robô emprega:
1. **Pausas Humanizadas Aleatórias (`humanizer.py`)**: Intervalos randômicos entre consultas e cliques.
2. **Intervalo entre Grupos**: Delays simulando atenção humana à tela antes de alterar o próximo grupo.
3. **Simulação de Digitação (`presence: composing`)**: Simula que o usuário está digitando ativamente no aplicativo durante 3 a 6 segundos antes de disparar avisos.
4. **Pausa Longa Pós-Fechamento**: Aguarda um tempo variável entre 1 e 7 minutos antes de notificar o grupo da coordenação.
