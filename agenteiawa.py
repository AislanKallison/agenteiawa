import os
import json
import requests
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Configurações da API Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
groq_client = Groq(api_key=GROQ_API_KEY)
MODELO_GROQ = "llama-3.1-8b-instant"

# Configurações da Evolution API
EVOLUTION_URL = "http://localhost:8080"
EVOLUTION_API_KEY = "rei_dos_lotes_token" 
INSTANCE_NAME = "rei_dos_lotes_key"

instrucao_sistema = (
    "Você é o corretor virtual oficial da 'Rei dos Lotes', uma imobiliária especialista em "
    "venda de terrenos e lotes residenciais e comerciais.\n"
    "Responda de forma livre e natural a QUALQUER pergunta ou dúvida que o cliente tiver, adaptando-se ao que ele falar. "
    "Sempre responda em português, de forma cordial, objetiva e use emojis (📍, 🏗️, 🤝).\n"
    "Seu foco principal é ser prestativo, tirar dúvidas de terrenos e tentar agendar uma visita ou coletar o nome/telefone para um corretor humano.\n"
    "Se não souber alguma informação específica de preço ou tamanho de um lote que não foi citado, peça educadamente o contato para enviar o PDF com a tabela atualizada."
)

historicos_conversas = {}

def obter_resposta_groq(id_conversa, texto_cliente):
    if id_conversa not in historicos_conversas:
        historicos_conversas[id_conversa] = [{"role": "system", "content": instrucao_sistema}]
    
    historicos_conversas[id_conversa].append({"role": "user", "content": texto_cliente})
    
    completion = groq_client.chat.completions.create(
        model=MODELO_GROQ,
        messages=historicos_conversas[id_conversa],
        temperature=0.7,
    )
    
    resposta = completion.choices[0].message.content
    historicos_conversas[id_conversa].append({"role": "assistant", "content": resposta})
    return resposta

def extrair_numero(key, message_data, remote_jid):
    """Tenta achar o número real de várias formas possíveis."""
    candidatos = [
        key.get("remoteJidAlt"),
        key.get("senderPn"),
        key.get("participant"),
        message_data.get("remoteJidAlt"),
        message_data.get("senderPn"),
        message_data.get("sender"),
        message_data.get("participant"),
    ]

    # Também procura em message_data inteiro por algo que termine com @s.whatsapp.net
    def procurar_jid(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                resultado = procurar_jid(v)
                if resultado:
                    return resultado
        elif isinstance(obj, str) and "@s.whatsapp.net" in obj:
            return obj
        return None

    jid_encontrado = procurar_jid(message_data)
    if jid_encontrado:
        candidatos.insert(0, jid_encontrado)

    for c in candidatos:
        if c and isinstance(c, str) and "@lid" not in c:
            # limpa e retorna só os dígitos (ou o jid limpo)
            numero = c.split("@")[0]
            if numero.isdigit() or numero:
                return numero

    # Último recurso: o próprio remote_jid (mesmo sendo @lid)
    return remote_jid

@app.route("/webhook", methods=["POST"])
@app.route("/webhook/messages-upsert", methods=["POST"])
def webhook():
    data = request.json
    
    try:
        if data.get("event") == "messages.upsert":
            message_data = data.get("data", {})
            key = message_data.get("key", {})
            
            from_me = key.get("fromMe", True)
            remote_jid = key.get("remoteJid", "")
            
            # Filtra mensagens enviadas por você mesmo ou vindas de grupos
            if not from_me and "@g.us" not in remote_jid:
                message = message_data.get("message", {})
                
                texto_cliente = (
                    message.get("conversation") or 
                    message.get("extendedTextMessage", {}).get("text", "")
                )
                
                if texto_cliente:
                    push_name = message_data.get("pushName", "Cliente")
                    
                    print(f"\n[Mensagem Recebida de {push_name}]")
                    print(f"[RemoteJid Original]: {remote_jid}")
                    print(f"[Texto]: {texto_cliente}")

                    # DEBUG: mostra o key e partes do payload para achar o número real
                    print(f"[DEBUG key]: {json.dumps(key, ensure_ascii=False, indent=2)}")
                    print(f"[DEBUG remoteJidAlt]: {key.get('remoteJidAlt')}")
                    print(f"[DEBUG senderPn]: {key.get('senderPn')}")
                    
                    resposta = obter_resposta_groq(remote_jid, texto_cliente)
                    print(f"[Resposta Gerada pelo Groq]:\n{resposta}\n")
                    
                    numero_envio = extrair_numero(key, message_data, remote_jid)
                    print(f"[Número para envio]: {numero_envio}")

                    headers = {
                        "apikey": EVOLUTION_API_KEY,
                        "Content-Type": "application/json"
                    }

                    url_send_text = f"{EVOLUTION_URL}/message/sendText/{INSTANCE_NAME}"

                    # Formato correto para Evolution 2.3.7
                    payload = {
                        "number": numero_envio,
                        "text": resposta,
                        "delay": 1200
                    }

                    res = requests.post(url_send_text, json=payload, headers=headers)
                    print(f"[Envio - status {res.status_code}]: {res.text}")

                    if res.status_code in [200, 201]:
                        print("✅ [SUCESSO] Resposta enviada com sucesso!")
                    else:
                        # Fallback ainda mais simples
                        payload2 = {
                            "number": numero_envio,
                            "text": resposta
                        }
                        res2 = requests.post(url_send_text, json=payload2, headers=headers)
                        print(f"[Envio simplificado - status {res2.status_code}]: {res2.text}")

                        if res2.status_code in [200, 201]:
                            print("✅ [SUCESSO] Resposta enviada com sucesso (formato simplificado)!")
                        else:
                            print(f"❌ [ERRO EVOLUTION]: {res2.text}")
                        
    except Exception as e:
        print(f"[Erro no Webhook]: {e}")
        
    return jsonify({"status": "SUCCESS"}), 200

if __name__ == "__main__":
    print("\nIniciando o Servidor do Agente Rei dos Lotes (Modo Definitivo Bypass LID)...")
    app.run(host="0.0.0.0", port=5000)
