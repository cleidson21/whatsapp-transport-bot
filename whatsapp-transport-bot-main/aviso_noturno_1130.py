import os
import logging
from json import JSONDecodeError
import requests
import random
import humanizer # O nosso escudo anti-ban

# ====== CONFIGURAÇÃO DE LOGS ======
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_api_automacao.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ====== CONFIGURAÇÕES DA API ======
API_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:8080")
API_KEY = os.getenv("WHATSAPP_API_KEY", "Transporte_Universitario_2026_Secreta")
NOME_INSTANCIA = os.getenv("WHATSAPP_INSTANCE", "sec-educ-berimbau")

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

# ====== CONFIGURAÇÕES DO FLUXO ======
GRUPOS_ALVO = [
    "Transporte FTC Noturno 2026",
    "Transporte FAN Noturno 2026",
    "Transporte FAT Noturno 2026",
    "Transporte UNIFACS Noturno 2026",
    "Transporte IFBA-UNEF Noturno 2026",
    "Transporte UEFS Noturno 2026",
    "Transporte SENAI-PITAGORAS Noturno 2026"
]

MENSAGEM_AVISO = "⚠️ *Aviso Sistema*: Lista fecha em 30 minutos!"

def carregar_grupos_alvo(grupos_padrao):
    grupos_env = os.getenv("WHATSAPP_GROUPS")
    if grupos_env:
        grupos = [grupo.strip() for grupo in grupos_env.split(";") if grupo.strip()]
        if grupos:
            return grupos
    return grupos_padrao

def normalizar_lista_grupos(resposta):
    if isinstance(resposta, dict):
        resposta = resposta.get("groups") or resposta.get("data") or []

    if not isinstance(resposta, list):
        logging.error(f"Resposta inesperada ao buscar grupos: {type(resposta).__name__}")
        return []

    return [grupo for grupo in resposta if isinstance(grupo, dict)]

def buscar_todos_os_grupos():
    """Baixa a lista de grupos da memória do WhatsApp de uma só vez."""
    logging.info("🔍 A carregar a lista de grupos para a memória...")
    url = f"{API_URL}/group/fetchAllGroups/{NOME_INSTANCIA}?getParticipants=false"
    
    try:
        resposta = requests.get(url, headers=headers, timeout=60)
        if resposta.status_code == 200:
            try:
                return normalizar_lista_grupos(resposta.json())
            except JSONDecodeError:
                logging.error("❌ A API devolveu uma resposta inválida ao carregar a lista de grupos.")
                return []
        else:
            logging.error(f"Erro na busca: HTTP {resposta.status_code}")
            return []
    except Exception as e:
        logging.error(f"❌ Erro de conexão: {e}")
        return []

def enviar_aviso(jid, nome_grupo, texto):
    """Envia a mensagem simulando o status de 'Digitando...' para humanização extra."""
    logging.info(f"✉️ A preparar envio para '{nome_grupo}'...")
    url = f"{API_URL}/message/sendText/{NOME_INSTANCIA}"
    
    # O truque de ouro está no 'delay'. Ele força o WhatsApp a mostrar 'Digitando...'
    # Sorteia um tempo de digitação entre 3 a 6 segundos.
    tempo_digitando_ms = random.randint(3000, 6000) 
    
    payload = {
        "number": jid,
        "text": texto,
        "delay": tempo_digitando_ms, 
        "presence": "composing" # Diz à Meta que o utilizador está a escrever ativamente
    }
    
    try:
        logging.info(f"⏳ Simulando digitação no grupo por {tempo_digitando_ms/1000:.1f} segundos...")
        # Timeout maior (15s) porque a requisição fica presa propositadamente enquanto simula a digitação
        resposta = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if resposta.status_code in [200, 201]:
            logging.info(f"✅ SUCESSO! Aviso enviado em: {nome_grupo}")
            return True
        else:
            logging.error(f"⚠️ Falha no envio para '{nome_grupo}': HTTP {resposta.status_code} - {resposta.text}")
            return False
    except Exception as e:
        logging.error(f"❌ Falha de rede ao enviar para '{nome_grupo}': {e}")
        return False

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    logging.info("=== INICIANDO AVISOS NOTURNOS (11:30H) ===")
    
    # Pausa de aquecimento do script
    humanizer.short_human_sleep(2.0, 5.0)
    
    todos_grupos = buscar_todos_os_grupos()
    grupos_alvo_ativos = carregar_grupos_alvo(GRUPOS_ALVO)
    
    if not todos_grupos:
        logging.error("A lista de grupos está vazia. Abortando operação.")
        exit()

    avisos_enviados = 0
    avisos_falhados = []
    
    for i, nome_alvo in enumerate(grupos_alvo_ativos):
        logging.info(f"--- Processando: {nome_alvo} ---")
        
        jid_grupo = next((g.get('id') for g in todos_grupos if g.get('subject') == nome_alvo), None)
        
        if jid_grupo:
            if enviar_aviso(jid_grupo, nome_alvo, MENSAGEM_AVISO):
                avisos_enviados += 1
            else:
                avisos_falhados.append(nome_alvo)
        else:
            logging.warning(f"⚠️ Grupo '{nome_alvo}' não encontrado.")
            avisos_falhados.append(nome_alvo)

        # Prevenção Absoluta contra Ban: Pausa longa entre cada envio, essencial já que são 7 grupos.
        if i < len(grupos_alvo_ativos) - 1:
            logging.info("⏳ Pausa de segurança (Transição para o próximo grupo)...")
            humanizer.look_at_screen_pause(12.0, 20.0)

    logging.info(f"📊 Resumo de Avisos: {avisos_enviados}/{len(grupos_alvo_ativos)} enviados com sucesso.")
    if avisos_falhados:
        logging.info(f"❌ Falhados: {avisos_falhados}")
        
    logging.info("🏁 Rotina de avisos (11:30H) finalizada.")