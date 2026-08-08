# Agente de IA – WhatsApp (agentedeia)

Atendimento automatizado no WhatsApp com Inteligência Artificial para a imobiliária **Rei dos Lotes**.

O bot recebe mensagens, gera respostas naturais com o modelo Llama (via Groq) e responde automaticamente os clientes 24h por dia. 

---

## 🛠️ Stack

| Tecnologia       | Função                                      |
|------------------|---------------------------------------------|
| Evolution API    | Conexão com WhatsApp (Baileys)              |
| Docker           | Container da Evolution API                  |
| Flask            | Servidor do webhook                         |
| Groq + Llama 3.1 | Geração de respostas inteligentes           |
| Python 3.10+     | Linguagem principal                         |

---

## 📁 # Agentedeia

(Código roda localmente, executando funções apenas com computador ligado. Caso deseje que ele rode 24/7 com funcionalidade, deve hospedar em vps na hostinger ou hostgator e utilizar a openclaw entre outros agentes que funcionam 24 horas na nuvem).
