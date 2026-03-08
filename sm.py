import requests
from datetime import datetime, timedelta

# ============================= TOKEN ===================================
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjIxMWIxZWUzLTM5NmQtNDU2NC1hZDNmLWQ2Y2NiYzRjM2VmZiIsInRva2VuVmVyc2lvbiI6MjkyLCJpYXQiOjE3NzIyNDkzMjAsImV4cCI6MTc3MjI3MDkyMH0.AYPCG8X3k8Y2Z7hNMNv8nkCauQRtT9PDa-TIT3vJnpo"

# CONFIGURACIÓN ========================================================== 
BASE_URL = "https://api.whaticket.com"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# CONFIGURACIÓN DE FECHAS
DIAS_A_SUMAR_TAG = 3
DIAS_A_SUMAR_PROGRAMADO1 = DIAS_A_SUMAR_TAG - 1  # 2 días
HORA_ENVIO_PROGRAMADO1 = 1  # 1 UTC = 8 PM Perú
DIAS_A_SUMAR_PROGRAMADO2 = DIAS_A_SUMAR_TAG  # 3 días
HORA_ENVIO_PROGRAMADO2 = 13  # 13 UTC = 8 AM Perú

# ACTIVADORES
ENVIAR_INMEDIATO = False  # True = enviar, False = no enviar
LIMITE_TICKETS = 1  # 0 = todos, >0 = solo los X primeros (para pruebas)

#============================ CONFIG - MAIN ====================================
# DEPARTAMENTOS, USUARIO, CONEXIONES (Definir nombres)
NOMBRE_QUEUE = "CONFIRMADO ALICOD"
NOMBRE_QUEUE_DESTINO = "REGISTRADO ALICOD" 
USER_ID_DESTINO = "33868160-85bb-4f2e-a31b-7f6913cc0501"  # 1MOTORIZADOS
USER_ID_ORIGEN = "0072f321-80f3-4361-8d05-1264220212d1"  # 1ALIDRIVER
CONNECTION_WHATSAPP = "Novedisimos" 
CONNECTION_BUSINESS = "Ds Print"

# PLANTILLAS WHATSAPP BUSINESS (Definir nombres de plantillas)
PLANTILLA_INMEDIATA = "not00" #Pide un valor 03/02
PLANTILLA_DIA_PREVIO = "not1"
PLANTILLA_DIA_LLEGADA = "2not"

# TEMPLATE IDs de WhatsApp Business
TEMPLATE_ID_NOT0 = "5e9d17a3-78f8-4efd-b13b-f33d05d35796"  # NOT0 - con parametro {{1}}
TEMPLATE_ID_NOT1 = "5e9d17a3-78f8-4efd-b13b-f33d05d35796"  # NOT1 - static
TEMPLATE_ID_NOT2 = "8f346952-3754-4aa3-9ed0-9045499db24e"  # NOT2 - static

# NOTAS RÁPIDAS (Textos de las notas rápidas - usar */* para fecha dinámica)
NOTA_RAPIDA_NOT0 = "*¡Hola, {{contactName}}😀!*\n\n¡Tu Pedido te lo entregaremos el */* en el rango de 10 am a 6 pm previamente el courier se contactará para indicarte una hora más exacta! 🚀\n\nNuestro equipo está trabajando en el empaquetado de tu pedido👥.\n\n*Muchas gracias, excelente día*🤝."
NOTA_RAPIDA_NOT1 = "*¡Buenas noticias, {{contactName}} 😀!*\n ¡Tu Pedido Está en Camino y Llegará *Mañana*!\n\n 🚀  Nuestro equipo está trabajando para que todo llegue a ti sin contratiempos👥.  \n\nGracias por confiar en nuestra empresa *NOVEDADES WOW SAC,* *Saludos Cordiales🤝*"
NOTA_RAPIDA_NOT2 = "Hola *{{contactName}}*😀😀,\n\n¡Estamos emocionados de contarte que *tu pedido está a punto de ser entregado*! 📦\n\nPara garantizar una entrega exitosa, te pedimos amablemente que respondas al motorizado que se pondrá en contacto contigo cuando esté cerca de tu ubicación. 🏍️🤳\n\n*Recuerda que nuestro rango de entrega es de 10 am a 6 pm, en caso no pueda recepcionarlo por favor dejar encargado*\n\n*Tu respuesta rápida ayudará a que el proceso sea más ágil y eficiente*.\n*¡Gracias por tu cooperación y confianza!*✅✅\n\nQue tengas un excelente día 🤝🤩"
#===============================================================================

# FUNCIONES ==========================
def obtener_tag_y_fecha():
    fecha_futura = datetime.now() + timedelta(days=DIAS_A_SUMAR_TAG)
    dia_tag = fecha_futura.strftime("%d")
    fecha_texto = fecha_futura.strftime("%d/%m")

    response = requests.get(f"{BASE_URL}/tag?pageNumber=1", headers=HEADERS)
    tags = response.json().get("tags", [])

    for tag in tags:
        if tag["name"] == dia_tag:
            return tag["id"], fecha_texto

    return None, fecha_texto

def obtener_queue_id(nombre_queue):
    response = requests.get(f"{BASE_URL}/queue", headers=HEADERS)
    queues = response.json()
    for queue in queues:
        if queue["name"] == nombre_queue:
            return queue["id"]
    return None

def obtener_tickets(queue_id, tag_id, user_id=None):
    all_tickets = []
    user_filter = f"&usersIds=[\"{user_id}\"]" if user_id else "&usersIds=[]"
    for page in range(1, 20):
        url = (
            f"{BASE_URL}/tickets?"
            f"pageNumber={page}&"
            f"status=%22open%22&"
            f"queueIds=[\"{queue_id}\"]&"
            f"{user_filter}&"
            f"includeAllPosts=true"
        )
        response = requests.get(url, headers=HEADERS)
        tickets = response.json().get("tickets", [])
        if not tickets:
            break
        for t in tickets:
            contact_tags = t.get('contact', {}).get('tags', [])
            tag_ids = [tag['id'] for tag in contact_tags]
            if tag_id in tag_ids:
                all_tickets.append(t)
    return all_tickets

def obtener_connection(connection_id):
    response = requests.get(f"{BASE_URL}/connections/{connection_id}", headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return None

def enviar_nota_rapida(ticket_id, nombre_nota, dias_sumar=0, hora_envio=None, contacto_nombre=""):
    """Envía una nota rápida de Whaticket usando el texto directo"""
    url = f"{BASE_URL}/messages/{ticket_id}"
    
    # Obtener el texto de la nota
    if nombre_nota == "NOT0":
        texto = NOTA_RAPIDA_NOT0
    elif nombre_nota == "NOT1":
        texto = NOTA_RAPIDA_NOT1
    elif nombre_nota == "NOT2":
        texto = NOTA_RAPIDA_NOT2
    else:
        texto = ""
    
    # Calcular fecha de entrega para NOT0
    fecha_entrega = datetime.now() + timedelta(days=DIAS_A_SUMAR_TAG)
    fecha_entrega_texto = fecha_entrega.strftime("%d/%m")
    
    # Reemplazar {{contactName}} con el nombre del contacto
    texto = texto.replace("{{contactName}}", contacto_nombre)
    
    # Reemplazar */* con la fecha de entrega (solo para NOT0)
    texto = texto.replace("*/*", fecha_entrega_texto)
    
    if dias_sumar == 0 and hora_envio is None:
        # Envío inmediato
        payload = {
            "body": texto,
            "fromMe": True,
            "isNote": False
        }
    else:
        # Programado
        fecha_programada = datetime.now() + timedelta(days=dias_sumar)
        hora = hora_envio if hora_envio is not None else 0
        fecha_programada = fecha_programada.replace(
            hour=hora, minute=0, second=0, microsecond=0
        )
        payload = {
            "body": texto,
            "fromMe": True,
            "isNote": False,
            "scheduleDate": fecha_programada.isoformat() + "Z",
            "signMessage": False
        }
    
    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"{nombre_nota}: {response.status_code}")
    return response

def enviar_plantilla_waba(ticket_id, nombre_plantilla, parametros=None, dias_sumar=0, hora_envio=None):
    """Envía plantilla de WhatsApp Business"""
    url = f"{BASE_URL}/messages/{ticket_id}"
    
    # Textos de las plantillas
    if nombre_plantilla == "NOT0":
        template_id = TEMPLATE_ID_NOT0
        body_texto = "*¡Hola😀!*\n\n¡Tu Pedido te lo entregaremos el *{{1}}* en el rango de 10 am a 6 pm previamente el courier se contactará para indicarte una hora más exacta! 🚀\n\nNuestro equipo está trabajando en el empaquetado de tu pedido👥.\n\n*Muchas gracias, excelente día*🤝."
    elif nombre_plantilla == "NOT1":
        template_id = TEMPLATE_ID_NOT1
        body_texto = "*¡Buenas noticias😀!*\n ¡Tu Pedido Está en Camino y Llegará *Mañana*!\n\n 🚀  Nuestro equipo está trabajando para que todo llegue a ti sin contratiempos👥.  \n\nGracias por confiar en nuestra empresa *NOVEDADES WOW SAC,* *Saludos Cordiales🤝*"
    elif nombre_plantilla == "NOT2":
        template_id = TEMPLATE_ID_NOT2
        body_texto = "Hola😀,\n¡Estamos emocionados de contarte que *tu pedido está a punto de ser entregado*! 📦\n\nPara garantizar una entrega exitosa, te pedimos amablemente que respondas al motorizado que se pondra en contacto contigo🏍️🤳\n\nQue tengas un excelente dia 🤝🤩"
    else:
        template_id = None
        body_texto = ""
    
    if dias_sumar == 0 and hora_envio is None:
        # Envío inmediato
        payload = {
            "body": body_texto,
            "fromMe": True,
            "isNote": False,
            "metadata": {
                "templateId": template_id,
                "parameters": [{"type": "text", "text": p} for p in parametros] if parametros else []
            }
        }
    else:
        # Programado
        fecha_programada = datetime.now() + timedelta(days=dias_sumar)
        hora = hora_envio if hora_envio is not None else 0
        fecha_programada = fecha_programada.replace(
            hour=hora, minute=0, second=0, microsecond=0
        )
        payload = {
            "body": body_texto,
            "fromMe": True,
            "isNote": False,
            "scheduleDate": fecha_programada.isoformat() + "Z",
            "signMessage": False,
            "metadata": {
                "templateId": template_id,
                "parameters": [{"type": "text", "text": p} for p in parametros] if parametros else []
            }
        }
    
    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"{nombre_plantilla}: {response.status_code}")
    return response

def transferir_ticket(ticket_id, queue_id, user_id):
    url = f"{BASE_URL}/tickets/{ticket_id}/transfer"
    payload = {"queueId": queue_id, "userId": user_id}
    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        print("OK")
    except requests.exceptions.HTTPError as e:
        print(f"Error: {e}")

# FLUJO PRINCIPAL ==========================
queue_id = obtener_queue_id(NOMBRE_QUEUE)
queue_id_destino = obtener_queue_id(NOMBRE_QUEUE_DESTINO)
tag_id, fecha_texto = obtener_tag_y_fecha()

if not tag_id:
    print(f"Tag {fecha_texto} no existe")
    exit()
if not queue_id or not queue_id_destino:
    print("Colas no encontradas")
    exit()

tickets = obtener_tickets(queue_id, tag_id, USER_ID_ORIGEN)
print(f"Tickets: {len(tickets)}")

if LIMITE_TICKETS > 0:
    tickets = tickets[:LIMITE_TICKETS]

for ticket in tickets:
    connection_id = ticket.get("connectionId")
    connection_data = obtener_connection(connection_id) if connection_id else None
    connection_name = connection_data.get("name") if connection_data else None

    ticket_id = ticket["id"]

    if connection_name == CONNECTION_WHATSAPP:
        # WhatsApp normal - usar notas rápidas
        nombre_contacto = ticket["contact"]["name"]
        if ENVIAR_INMEDIATO:
            enviar_nota_rapida(ticket_id, "NOT0", 0, None, nombre_contacto)
        enviar_nota_rapida(ticket_id, "NOT1", DIAS_A_SUMAR_PROGRAMADO1, HORA_ENVIO_PROGRAMADO1, nombre_contacto)
        enviar_nota_rapida(ticket_id, "NOT2", DIAS_A_SUMAR_PROGRAMADO2, HORA_ENVIO_PROGRAMADO2, nombre_contacto)

        # Transferencia desactivada
        transferir_ticket(ticket_id, queue_id_destino, USER_ID_DESTINO)

    elif connection_name == CONNECTION_BUSINESS:
        # WhatsApp Business - usar plantillas
        # Calcular fecha para NOT0
        fecha_entrega = datetime.now() + timedelta(days=DIAS_A_SUMAR_TAG)
        fecha_entrega_texto = fecha_entrega.strftime("%d/%m")
        
        if ENVIAR_INMEDIATO:
            enviar_plantilla_waba(ticket_id, "NOT0", [fecha_entrega_texto], 0, None)
        enviar_plantilla_waba(ticket_id, "NOT1", None, DIAS_A_SUMAR_PROGRAMADO1+1 , HORA_ENVIO_PROGRAMADO1)
        enviar_plantilla_waba(ticket_id, "NOT2", None, DIAS_A_SUMAR_PROGRAMADO2, HORA_ENVIO_PROGRAMADO2)

        # Transferencia desactivada
        transferir_ticket(ticket_id, queue_id_destino, USER_ID_DESTINO)
