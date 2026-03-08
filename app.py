import customtkinter as ctk
import threading
import requests
from datetime import datetime, timedelta
from tkinter import messagebox

# ============================= CONFIGURACIÓN ============================
# (Los valores se actualizarán desde la GUI)

BASE_URL = "https://api.whaticket.com"

# CONFIG - MAIN
NOMBRE_QUEUE = "CONFIRMADO ALICOD"
NOMBRE_QUEUE_DESTINO = "REGISTRADO ALICOD"
USER_ID_DESTINO = "33868160-85bb-4f2e-a31b-7f6913cc0501"
USER_ID_ORIGEN = "0072f321-80f3-4361-8d05-1264220212d1"
CONNECTION_WHATSAPP = "Novedisimos"
CONNECTION_BUSINESS = "Ds Print"

# TEMPLATE IDs
TEMPLATE_ID_NOT0 = "5e9d17a3-78f8-4efd-b13b-f33d05d35796"
TEMPLATE_ID_NOT1 = "5e9d17a3-78f8-4efd-b13b-f33d05d35796"
TEMPLATE_ID_NOT2 = "8f346952-3754-4aa3-9ed0-9045499db24e"

# NOTAS RÁPIDAS
NOTA_RAPIDA_NOT0 = "*¡Hola, {{contactName}}😀!*\n\n¡Tu Pedido te lo entregaremos el */* en el rango de 10 am a 6 pm previamente el courier se contactará para indicarte una hora más exacta! 🚀\n\nNuestro equipo está trabajando en el empaquetado de tu pedido👥.\n\n*Muchas gracias, excelente día*🤝."
NOTA_RAPIDA_NOT1 = "*¡Buenas noticias, {{contactName}} 😀!*\n ¡Tu Pedido Está en Camino y Llegará *Mañana*!\n\n 🚀  Nuestro equipo está trabajando para que todo llegue a ti sin contratiempos👥.  \n\nGracias por confiar en nuestra empresa *NOVEDADES WOW SAC,* *Saludos Cordiales🤝*"
NOTA_RAPIDA_NOT2 = "Hola *{{contactName}}*😀😀,\n\n¡Estamos emocionados de contarte que *tu pedido está a punto de ser entregado*! 📦\n\nPara garantizar una entrega exitosa, te pedimos amablemente que respondas al motorizado que se pondra en contacto contigo🏍️🤳\n\nQue tengas un excelente dia 🤝🤩"

# Variables que se actualizarán desde la GUI
TOKEN = ""
HEADERS = {}
DIAS_A_SUMAR_TAG = 0
ENVIAR_INMEDIATO = False
LIMITE_TICKETS = 0

HORA_ENVIO_PROGRAMADO1 = 1   # 1 UTC = 8 PM Perú
HORA_ENVIO_PROGRAMADO2 = 13  # 13 UTC = 8 AM Perú


# ============================= FUNCIONES API ============================

def obtener_tag_y_fecha():
    """Obtiene el tag basado en DIAS_A_SUMAR_TAG"""
    fecha_futura = datetime.now() + timedelta(days=DIAS_A_SUMAR_TAG)
    dia_tag = fecha_futura.strftime("%d")
    fecha_texto = fecha_futura.strftime("%d/%m")

    response = requests.get(f"{BASE_URL}/tag?pageNumber=1", headers=HEADERS)
    data = response.json()
    
    if not isinstance(data, dict):
        print(f"Debug: tag response = {data}")
        return None, fecha_texto
    
    tags = data.get("tags", [])
    
    if not isinstance(tags, list):
        print(f"Debug: tags = {tags}")
        return None, fecha_texto
    
    for tag in tags:
        if isinstance(tag, dict) and tag.get("name") == dia_tag:
            return tag["id"], fecha_texto

    return None, fecha_texto


def obtener_queue_id(nombre_queue):
    response = requests.get(f"{BASE_URL}/queue", headers=HEADERS)
    queues = response.json()
    
    if not isinstance(queues, list):
        print(f"Debug: queues response = {queues}")
        return None
    
    for queue in queues:
        if isinstance(queue, dict) and queue.get("name") == nombre_queue:
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
        data = response.json()
        
        if not isinstance(data, dict):
            print(f"Debug: tickets response page {page} = {data}")
            break
            
        tickets = data.get("tickets", [])
        
        if not isinstance(tickets, list):
            print(f"Debug: tickets = {tickets}")
            break
            
        if not tickets:
            break
            
        for t in tickets:
            if not isinstance(t, dict):
                continue
            contact = t.get('contact', {})
            if isinstance(contact, dict):
                contact_tags = contact.get('tags', [])
                if isinstance(contact_tags, list):
                    tag_ids = [tag.get('id') for tag in contact_tags if isinstance(tag, dict)]
                    if tag_id in tag_ids:
                        all_tickets.append(t)
    return all_tickets


def obtener_connection(connection_id):
    response = requests.get(f"{BASE_URL}/connections/{connection_id}", headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return None


def enviar_nota_rapida(ticket_id, nombre_nota, dias_sumar=0, hora_envio=None, contacto_nombre=""):
    url = f"{BASE_URL}/messages/{ticket_id}"
    
    if nombre_nota == "NOT0":
        texto = NOTA_RAPIDA_NOT0
    elif nombre_nota == "NOT1":
        texto = NOTA_RAPIDA_NOT1
    elif nombre_nota == "NOT2":
        texto = NOTA_RAPIDA_NOT2
    else:
        texto = ""
    
    fecha_entrega = datetime.now() + timedelta(days=DIAS_A_SUMAR_TAG)
    fecha_entrega_texto = fecha_entrega.strftime("%d/%m")
    
    texto = texto.replace("{{contactName}}", contacto_nombre)
    texto = texto.replace("*/*", fecha_entrega_texto)
    
    if dias_sumar == 0 and hora_envio is None:
        payload = {
            "body": texto,
            "fromMe": True,
            "isNote": False
        }
    else:
        fecha_programada = datetime.now() + timedelta(days=dias_sumar)
        hora = hora_envio if hora_envio is not None else 0
        fecha_programada = fecha_programada.replace(hour=hora, minute=0, second=0, microsecond=0)
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
    url = f"{BASE_URL}/messages/{ticket_id}"
    
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
    
    # Reemplazar {{1}} con parametros
    if parametros:
        for i, param in enumerate(parametros, 1):
            body_texto = body_texto.replace(f"{{{{{i}}}}}", param)
    
    if dias_sumar == 0 and hora_envio is None:
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
        fecha_programada = datetime.now() + timedelta(days=dias_sumar)
        hora = hora_envio if hora_envio is not None else 0
        fecha_programada = fecha_programada.replace(hour=hora, minute=0, second=0, microsecond=0)
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


# ============================= INTERFAZ GRÁFICA ============================

class ConfigApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Massive Nots")
        self.geometry("500x650")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.ejecutando = False

        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # TOKEN
        self.label_token = ctk.CTkLabel(self.main_frame, text="TOKEN", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_token.pack(anchor="w", pady=(5, 3))

        self.label_token_desc = ctk.CTkLabel(
            self.main_frame,
            text="Ingresa tu TOKEN (Authorization: Bearer)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.label_token_desc.pack(anchor="w", pady=(0, 3))

        self.entry_token = ctk.CTkEntry(self.main_frame, placeholder_text="Ejemplo: eyJhbGciOiJIUzI...", height=35)
        self.entry_token.pack(fill="x", pady=(0, 10))

        # DIAS A SUMAR
        self.label_dias = ctk.CTkLabel(self.main_frame, text="DIAS A SUMAR", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_dias.pack(anchor="w", pady=(5, 3))

        self.label_dias_desc = ctk.CTkLabel(
            self.main_frame,
            text="Si hoy es 2 y el tag buscado es 5, deberas escribir 3 aqui",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.label_dias_desc.pack(anchor="w", pady=(0, 3))

        self.entry_dias = ctk.CTkEntry(self.main_frame, placeholder_text="Ejemplo: 3", height=35, width=100)
        self.entry_dias.pack(anchor="w", pady=(0, 10))

        # LIMITE DE CLIENTES
        self.label_limite = ctk.CTkLabel(self.main_frame, text="LIMITE DE CLIENTES", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_limite.pack(anchor="w", pady=(5, 3))

        self.label_descripcion = ctk.CTkLabel(
            self.main_frame,
            text="A cuantos clientes deseas enviar el mensaje?",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.label_descripcion.pack(anchor="w", pady=(0, 3))

        self.entry_limite = ctk.CTkEntry(self.main_frame, placeholder_text="Ejemplo: 50", height=35)
        self.entry_limite.pack(fill="x", pady=(0, 10))

        # ENVIAR INMEDIATO
        self.label_enviar_inmediato = ctk.CTkLabel(self.main_frame, text="Desea enviar el Not0?", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_enviar_inmediato.pack(anchor="w", pady=(10, 3))

        self.switch_enviar = ctk.CTkSwitch(self.main_frame, text="", onvalue=True, offvalue=False)
        self.switch_enviar.deselect()
        self.switch_enviar.pack(anchor="w", pady=(0, 10))

        # ADVERTENCIA
        self.frame_advertencia = ctk.CTkFrame(self.main_frame, fg_color="#3D1E1E", corner_radius=10)
        self.frame_advertencia.pack(fill="x", pady=(5, 10))

        self.label_advertencia = ctk.CTkLabel(
            self.frame_advertencia,
            text="Este programa siempre enviara NOT1, NOT2\ny transferira automaticamente al departamento\nde REGISTRADOS ALICOD",
            font=ctk.CTkFont(size=11),
            text_color="#FF6B6B"
        )
        self.label_advertencia.pack(padx=10, pady=8)

        # BARRA DE PROGRESO
        self.label_progreso = ctk.CTkLabel(self.main_frame, text="Progreso: 0%", font=ctk.CTkFont(size=12, weight="bold"))
        self.label_progreso.pack(anchor="w", pady=(5, 2))

        self.barra_progreso = ctk.CTkProgressBar(self.main_frame, height=15, progress_color="#2FA572")
        self.barra_progreso.pack(fill="x", pady=(0, 10))
        self.barra_progreso.set(0)

        # BOTON EJECUTAR
        self.btn_ejecutar = ctk.CTkButton(
            self.main_frame,
            text="EJECUTAR ENVIO",
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.ejecutar_envio,
            fg_color="#2FA572",
            hover_color="#1E7A4F"
        )
        self.btn_ejecutar.pack(fill="x", pady=(5, 0))

    def guardar_configuracion(self) -> bool:
        global TOKEN, HEADERS, DIAS_A_SUMAR_TAG, ENVIAR_INMEDIATO, LIMITE_TICKETS

        TOKEN = self.entry_token.get().strip()

        if not TOKEN:
            self.mostrar_error("Por favor ingresa un TOKEN")
            return False

        dias_text = self.entry_dias.get().strip()
        if not dias_text or not dias_text.isdigit() or len(dias_text) != 1:
            self.mostrar_error("DIAS A SUMAR debe ser 1 digito (ej: 3)")
            return False
        DIAS_A_SUMAR_TAG = int(dias_text)

        limite_text = self.entry_limite.get().strip()
        if not limite_text or not limite_text.isdigit():
            self.mostrar_error("LIMITE DE CLIENTES debe ser un numero")
            return False
        LIMITE_TICKETS = int(limite_text)

        ENVIAR_INMEDIATO = self.switch_enviar.get()

        # Actualizar HEADERS con el TOKEN del usuario
        HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

        return True

    def mostrar_error(self, mensaje: str):
        messagebox.showerror("Error", mensaje)

    def actualizar_progreso(self, porcentaje: float):
        self.barra_progreso.set(porcentaje)
        self.label_progreso.configure(text=f"Progreso: {int(porcentaje * 100)}%")
        self.update_idletasks()

    def ejecutar_envio(self):
        if self.ejecutando:
            self.mostrar_error("El proceso ya esta en ejecucion")
            return

        if not self.guardar_configuracion():
            return

        self.ejecutando = True
        self.btn_ejecutar.configure(state="disabled", text="ENVIANDO...")

        print(f"TOKEN: {TOKEN[:20]}...")
        print(f"DIAS_A_SUMAR_TAG: {DIAS_A_SUMAR_TAG}")

        hilo = threading.Thread(target=self._proceso_envio, daemon=True)
        hilo.start()

    def _proceso_envio(self):
        try:
            self.after(0, lambda: self.actualizar_progreso(0.05))

            queue_id = obtener_queue_id(NOMBRE_QUEUE)
            queue_id_destino = obtener_queue_id(NOMBRE_QUEUE_DESTINO)
            tag_id, fecha_texto = obtener_tag_y_fecha()

            if not tag_id:
                self.after(0, lambda: self.mostrar_error(f"Tag dia {DIAS_A_SUMAR_TAG} no existe"))
                self._fin_ejecucion()
                return

            if not queue_id or not queue_id_destino:
                self.after(0, lambda: self.mostrar_error("Colas no encontradas"))
                self._fin_ejecucion()
                return

            self.after(0, lambda: self.actualizar_progreso(0.1))

            tickets = obtener_tickets(queue_id, tag_id, USER_ID_ORIGEN)

            if LIMITE_TICKETS > 0:
                tickets = tickets[:LIMITE_TICKETS]

            total_tickets = len(tickets)

            if total_tickets == 0:
                self.after(0, lambda: self.mostrar_error("No se encontraron tickets"))
                self._fin_ejecucion()
                return

            for i, ticket in enumerate(tickets):
                if not isinstance(ticket, dict):
                    continue
                    
                progreso_base = 0.1
                progreso_max = 0.95
                progreso = progreso_base + (progreso_max - progreso_base) * (i / total_tickets)
                self.after(0, lambda p=progreso: self.actualizar_progreso(p))

                connection_id = ticket.get("connectionId")
                connection_data = obtener_connection(connection_id) if connection_id else None
                
                if isinstance(connection_data, dict):
                    connection_name = connection_data.get("name")
                else:
                    connection_name = None
                    
                ticket_id = ticket.get("id")
                if not ticket_id:
                    continue

                contact = ticket.get("contact")
                if isinstance(contact, dict):
                    nombre_contacto = contact.get("name", "Cliente")
                else:
                    nombre_contacto = "Cliente"

                if connection_name == CONNECTION_WHATSAPP:
                    if ENVIAR_INMEDIATO:
                        enviar_nota_rapida(ticket_id, "NOT0", 0, None, nombre_contacto)
                    enviar_nota_rapida(ticket_id, "NOT1", DIAS_A_SUMAR_TAG - 1, HORA_ENVIO_PROGRAMADO1, nombre_contacto)
                    enviar_nota_rapida(ticket_id, "NOT2", DIAS_A_SUMAR_TAG, HORA_ENVIO_PROGRAMADO2, nombre_contacto)
                    transferir_ticket(ticket_id, queue_id_destino, USER_ID_DESTINO)

                elif connection_name == CONNECTION_BUSINESS:
                    fecha_entrega = datetime.now() + timedelta(days=DIAS_A_SUMAR_TAG)
                    fecha_entrega_texto = fecha_entrega.strftime("%d/%m")

                    if ENVIAR_INMEDIATO:
                        enviar_plantilla_waba(ticket_id, "NOT0", [fecha_entrega_texto], 0, None)
                    enviar_plantilla_waba(ticket_id, "NOT1", None, DIAS_A_SUMAR_TAG, HORA_ENVIO_PROGRAMADO1)
                    enviar_plantilla_waba(ticket_id, "NOT2", None, DIAS_A_SUMAR_TAG + 1, HORA_ENVIO_PROGRAMADO2)
                    transferir_ticket(ticket_id, queue_id_destino, USER_ID_DESTINO)

            self.after(0, lambda: self.actualizar_progreso(1.0))
            self._fin_ejecucion()

        except Exception as e:
            import traceback
            print(f"Error: {str(e)}\n{traceback.format_exc()}")
            self.after(0, lambda msg=str(e): self.mostrar_error(f"Error: {msg}"))
            self._fin_ejecucion()

    def _fin_ejecucion(self):
        self.ejecutando = False
        self.btn_ejecutar.configure(state="normal", text="EJECUTAR ENVIO")


def main():
    app = ConfigApp()
    app.mainloop()


if __name__ == "__main__":
    main()
