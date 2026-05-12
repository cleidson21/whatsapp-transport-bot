import os
import time
import logging
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
API_URL = "http://localhost:8080"
API_KEY = "Transporte_Universitario_2026_Secreta"
NOME_INSTANCIA = "sec-educ-berimbau"

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

# ====== CONFIGURAÇÕES DO FLUXO (NOTURNO) ======
GRUPOS_ALVO = [
    "Transporte SENAI-PITAGORAS Noturno 2026",
    "Transporte UEFS Noturno 2026",
    "Transporte IFBA-UNEF Noturno 2026",
    "Transporte UNIFACS Noturno 2026",
    "Transporte FAT Noturno 2026",
    "Transporte FAN Noturno 2026",
    "Transporte FTC Noturno 2026"
]

GRUPO_COORDENACAO = "Operação Transporte Universitário"

MENSAGEM_FECHAMENTO = "❌✖️❌✖️Lista Fechada ❌✖️❌✖️"
MENSAGEM_SOLICITAR_LISTA = "Por favor, enviar a lista do turno fechado: NOTURNO."

def buscar_todos_os_grupos():
    """Baixa a lista de grupos da memória do WhatsApp de uma só vez."""
    logging.info("🔍 A carregar a lista de grupos para a memória...")
    url = f"{API_URL}/group/fetchAllGroups/{NOME_INSTANCIA}?getParticipants=false"
    
    try:
        resposta = requests.get(url, headers=headers, timeout=60)
        if resposta.status_code == 200:
            return resposta.json()
        return []
    except Exception as e:
        logging.error(f"❌ Erro de conexão: {e}")
        return []

def fechar_permissoes_grupo(jid, nome_grupo):
    """Envia o comando POST para trancar o grupo (Apenas Admins)."""
    logging.info(f"🔒 A enviar ordem para FECHAR o grupo '{nome_grupo}'...")
    url = f"{API_URL}/group/updateSetting/{NOME_INSTANCIA}"
    
    # action: 'announcement' -> Tranca o grupo (Apenas administradores podem enviar)
    payload = {
        "groupJid": jid,
        "action": "announcement" 
    }
    
    try:
        resposta = requests.post(url, json=payload, headers=headers, timeout=60)
        if resposta.status_code in [200, 201]:
            logging.info(f"🔒 SUCESSO! O grupo '{nome_grupo}' foi FECHADO.")
            return True
        else:
            logging.error(f"⚠️ Erro ao fechar '{nome_grupo}': HTTP {resposta.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ Falha ao enviar o comando de fechamento: {e}")
        return False

def enviar_mensagem(jid, nome_grupo, texto):
    """Envia a mensagem simulando digitação humana."""
    url = f"{API_URL}/message/sendText/{NOME_INSTANCIA}"
    tempo_digitando_ms = random.randint(3000, 5000) 
    
    payload = {
        "number": jid,
        "text": texto,
        "delay": tempo_digitando_ms, 
        "presence": "composing" 
    }
    
    try:
        logging.info(f"⏳ Simulando digitação em '{nome_grupo}' por {tempo_digitando_ms/1000:.1f} segundos...")
        resposta = requests.post(url, json=payload, headers=headers, timeout=60)
        if resposta.status_code in [200, 201]:
            logging.info(f"✉️ Mensagem enviada com sucesso em: {nome_grupo}")
            return True
        return False
    except Exception as e:
        logging.error(f"❌ Falha ao enviar mensagem para '{nome_grupo}': {e}")
        return False

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    logging.info("=== INICIANDO FECHAMENTO NOTURNO (12H) ===")
    
    humanizer.short_human_sleep(2.0, 5.0)
    todos_grupos = buscar_todos_os_grupos()
    
    if not todos_grupos:
        logging.error("A lista de grupos está vazia. Abortando operação.")
        exit()

    grupos_fechados = 0
    
    # 1. FECHAR OS GRUPOS DOS ALUNOS
    for i, nome_alvo in enumerate(GRUPOS_ALVO):
        logging.info(f"--- Processando: {nome_alvo} ---")
        jid_grupo = next((g.get('id') for g in todos_grupos if g.get('subject') == nome_alvo), None)
        
        if jid_grupo:
            # Tenta fechar o grupo
            if fechar_permissoes_grupo(jid_grupo, nome_alvo):
                # Se fechou, espera entre 1.5 e 3 segundos antes de mandar a mensagem de fechamento
                humanizer.short_human_sleep(1.5, 3.0)
                # Envia a mensagem com os Xs
                enviar_mensagem(jid_grupo, nome_alvo, MENSAGEM_FECHAMENTO)
                grupos_fechados += 1
        else:
            logging.warning(f"⚠️ Grupo '{nome_alvo}' não encontrado.")

        # Pausa de transição entre grupos
        if i < len(GRUPOS_ALVO) - 1:
            logging.info("⏳ Transição para o próximo grupo...")
            humanizer.look_at_screen_pause(10.0, 18.0)

    # 2. A MAGIA ANTI-BAN: O GRANDE DELAY PARA O GRUPO DE COORDENAÇÃO
    # Aguarda um tempo altamente inconsistente (entre 1 e 7 minutos)
    tempo_cafe_segundos = random.randint(60, 420)
    minutos = tempo_cafe_segundos // 60
    segundos = tempo_cafe_segundos % 60
    
    logging.info("="*50)
    logging.info(f"☕ Pausa longa de Operação! O robô vai aguardar {minutos}m e {segundos}s antes de pedir a lista.")
    logging.info("="*50)
    
    time.sleep(tempo_cafe_segundos)

    # 3. PEDIR A LISTA À COORDENAÇÃO
    logging.info("--- Retomando: Processando Grupo de Coordenação ---")
    jid_coordenacao = next((g.get('id') for g in todos_grupos if g.get('subject') == GRUPO_COORDENACAO), None)
    
    if jid_coordenacao:
        enviar_mensagem(jid_coordenacao, GRUPO_COORDENACAO, MENSAGEM_SOLICITAR_LISTA)
    else:
        logging.error(f"⚠️ GRUPO CRÍTICO NÃO ENCONTRADO: '{GRUPO_COORDENACAO}'.")

    logging.info("🏁 Processo de fechamento noturno finalizado com sucesso.")