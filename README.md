# WhatsApp Transport Hub - Centralized Automation & Anti-Ban Bot

<p align="center">
  <a href="README.md"><b>English</b></a> • <a href="README.pt-BR.md"><b>Português</b></a>
</p>

An automated hub for orchestrating, opening, warning, and locking student transportation groups on WhatsApp using the **Evolution API** (Baileys engine), **Docker Compose**, and humanized anti-ban heuristics.

---

## Architecture Overview

This project was built to replace dispersed cron scripts with a centralized, containerized hub. All operational routines (opening rosters, sending 30-minute advance warnings, locking group chat permissions, and requesting final rosters to dispatch coordinators) are orchestrated by a single Python service reading dynamic schedules from `config.json`.

```text
                  +---------------------------+
                  |  Evolution Manager (UI)   |  (Port 3000)
                  +-------------+-------------+
                                |
+-----------------+   +---------v---------+   +-------------------+
|  PostgreSQL 15  |<->|   Evolution API   |<->|   Redis (Cache)   |
+-----------------+   +---------^---------+   +-------------------+
                                |  (Port 8080)
                      +---------+---------+
                      |      hub_bot      |  (Python Scheduler)
                      |   [config.json]   |
                      +-------------------+
```

### Stack Components

- **`hub_bot`**: Python 3.10 daemon handling cron-like dispatching via `schedule` with randomized humanized timeouts and anti-ban heuristics.
- **`evolution_api`**: REST API bridging WhatsApp multi-device sockets via Baileys engine.
- **`evolution_frontend`**: Web dashboard (Evolution Manager) for QR code pairing and instance monitoring.
- **`postgres`**: Relational persistence for instances, tokens, and sessions.
- **`redis`**: Message broker, state cache, and lock queue.

---

## Anti-Ban & Humanization Heuristics

To protect bot phone numbers against Meta spam detection algorithms, the service enforces several behavioral guards:

1. **Schedule Jitter:** Instead of triggering at exact zero-second marks (e.g., `07:00:00`), jobs apply an initial random delay (15s to 45s) before executing.
2. **Template Shuffling:** Warning announcements are randomly picked from cohesive, professional templates to prevent repeated message hashing across groups.
3. **Simulated Typing (`presence: composing`):** The bot signals active user typing for 4 to 7.5 seconds before dispatching any notification.
4. **Inter-Group Pauses:** 12 to 35 second inspection delays are enforced between updating successive groups (`look_at_screen_pause`).
5. **Operational Cooldown:** After locking group rosters, the bot waits 1 to 5 minutes before pinging the coordination dispatch group.

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/cleidson21/whatsapp-transport-bot.git
cd whatsapp-transport-bot
```

### 2. Configure Environment & Groups
Copy the example files:
```bash
cp .env.example .env
cp config.example.json config.json
```
- Edit `.env` to set your PostgreSQL passwords and Evolution API keys.
- Edit `config.json` with your WhatsApp group names and target hours.

### 3. Launch Services
```bash
docker compose up -d --build
```

### 4. Pair WhatsApp via QR Code
1. Open [http://localhost:3000](http://localhost:3000) (or create an SSH tunnel if on a remote VPS: `ssh -L 3000:localhost:3000 -L 8080:localhost:8080 user@vps-ip`).
2. Log into the Evolution Manager using your `AUTHENTICATION_API_KEY`.
3. Create an instance matching `WHATSAPP_INSTANCE` (default: `transporte-hub`).
4. Scan the rendered QR Code using WhatsApp on your device (*Linked Devices > Link a Device*).

### 5. Monitor Logs
```bash
docker compose logs -f hub_bot
```

To stop the services:
```bash
docker compose down
```

---

## Schedule & Group Configuration (`config.json`)

All shifts, schedules, and targets are decoupled from source code and dynamically loaded:

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

*Note: The engine supports both English (`coordination_group`, `shifts`, `schedules`, `open`, `warn`, `close`, `groups`) and Portuguese (`grupo_coordenacao`, `turnos`, `horarios`, `abrir`, `avisar`, `fechar`, `grupos`) configuration keys.*

---

## Environment Variables (`.env`)

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `POSTGRES_DATABASE` | PostgreSQL database name | `evolution` |
| `POSTGRES_USERNAME` | PostgreSQL database user | `evolution` |
| `POSTGRES_PASSWORD` | PostgreSQL database password | `your_postgres_password_here` |
| `AUTHENTICATION_API_KEY` | Master API Key for Evolution API | `your_evolution_api_global_key_here` |
| `SERVER_URL` | Evolution API public / external URL | `http://localhost:8080` |
| `WHATSAPP_API_URL` | Internal Evolution API endpoint for the bot | `http://evolution_api:8080` |
| `WHATSAPP_API_KEY` | Instance / Global key used by the bot | `your_evolution_api_global_key_here` |
| `WHATSAPP_INSTANCE` | WhatsApp instance name | `transporte-hub` |
| `WHATSAPP_COORDINATION_GROUP` | (Optional) Override coordination group name | `Coordination Dispatch Group` |

---

## License

This project is licensed under the [MIT License](LICENSE).
