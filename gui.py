import customtkinter as ctk
import threading

# Constantes globales
TOKEN: str = ""
DIAS_A_SUMAR_TAG: int = 0
LIMITE_TICKETS: int = 0
ENVIAR_INMEDIATO: bool = False


class ConfigApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Massive Nots - by Komodo")
        self.geometry("500x650")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.ejecutando = False

        # Contenedor principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # TOKEN
        self.label_token = ctk.CTkLabel(
            self.main_frame,
            text="TOKEN",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label_token.pack(anchor="w", pady=(5, 3))

        self.label_token_desc = ctk.CTkLabel(
            self.main_frame,
            text="Ingresa tu TOKEN (Authorization: Bearer)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.label_token_desc.pack(anchor="w", pady=(0, 3))

        self.entry_token = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="Ejemplo: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Im...",
            height=35
        )
        self.entry_token.pack(fill="x", pady=(0, 10))

        # DIAS A SUMAR
        self.label_dias = ctk.CTkLabel(
            self.main_frame,
            text="DIAS A SUMAR",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label_dias.pack(anchor="w", pady=(5, 3))

        self.label_dias_desc = ctk.CTkLabel(
            self.main_frame,
            text="Si hoy es 2 y el tag buscado es 5, deberas escribir 3 aqui",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.label_dias_desc.pack(anchor="w", pady=(0, 3))

        self.entry_dias = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="Ejemplo: 3",
            height=35,
            width=100
        )
        self.entry_dias.pack(anchor="w", pady=(0, 10))

        # LIMITE DE CLIENTES
        self.label_limite = ctk.CTkLabel(
            self.main_frame,
            text="LIMITE DE CLIENTES",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label_limite.pack(anchor="w", pady=(5, 3))

        self.label_descripcion = ctk.CTkLabel(
            self.main_frame,
            text="A cuantos clientes deseas enviar el mensaje?",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.label_descripcion.pack(anchor="w", pady=(0, 3))

        self.entry_limite = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="Ejemplo: 50",
            height=35
        )
        self.entry_limite.pack(fill="x", pady=(0, 10))

        # ENVIAR INMEDIATO
        self.label_enviar_inmediato = ctk.CTkLabel(
            self.main_frame,
            text="Desea enviar el Not0?",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.label_enviar_inmediato.pack(anchor="w", pady=(10, 3))

        self.switch_enviar = ctk.CTkSwitch(
            self.main_frame,
            text="",
            onvalue=True,
            offvalue=False
        )
        self.switch_enviar.deselect()
        self.switch_enviar.pack(anchor="w", pady=(0, 10))

        # ADVERTENCIA
        self.frame_advertencia = ctk.CTkFrame(
            self.main_frame,
            fg_color="#3D1E1E",
            corner_radius=10
        )
        self.frame_advertencia.pack(fill="x", pady=(5, 10))

        self.label_advertencia = ctk.CTkLabel(
            self.frame_advertencia,
            text="Este programa siempre enviara NOT1, NOT2\ny transferira automaticamente al departamento\nde REGISTRADOS ALICOD",
            font=ctk.CTkFont(size=11),
            text_color="#FF6B6B"
        )
        self.label_advertencia.pack(padx=10, pady=8)

        # BARRA DE PROGRESO
        self.label_progreso = ctk.CTkLabel(
            self.main_frame,
            text="Progreso: 0%",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.label_progreso.pack(anchor="w", pady=(5, 2))

        self.barra_progreso = ctk.CTkProgressBar(
            self.main_frame,
            height=15,
            progress_color="#2FA572"
        )
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
        global TOKEN, DIAS_A_SUMAR_TAG, LIMITE_TICKETS, ENVIAR_INMEDIATO

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
        return True

    def mostrar_error(self, mensaje: str):
        from tkinter import messagebox
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

        hilo = threading.Thread(target=self._proceso_envio, daemon=True)
        hilo.start()

    def _proceso_envio(self):
        try:
            from sm import (
                HEADERS, BASE_URL, NOMBRE_QUEUE, NOMBRE_QUEUE_DESTINO,
                USER_ID_DESTINO, USER_ID_ORIGEN,
                obtener_queue_id, obtener_tag_y_fecha, obtener_tickets,
                obtener_connection, enviar_nota_rapida, enviar_plantilla_waba,
                transferir_ticket, CONNECTION_WHATSAPP, CONNECTION_BUSINESS,
                DIAS_A_SUMAR_PROGRAMADO1, HORA_ENVIO_PROGRAMADO1,
                DIAS_A_SUMAR_PROGRAMADO2, HORA_ENVIO_PROGRAMADO2
            )
            from datetime import datetime, timedelta

            self.after(0, lambda: self.actualizar_progreso(0.05))

            queue_id = obtener_queue_id(NOMBRE_QUEUE)
            queue_id_destino = obtener_queue_id(NOMBRE_QUEUE_DESTINO)
            tag_id, fecha_texto = obtener_tag_y_fecha()

            if not tag_id:
                self.after(0, lambda: self.mostrar_error(f"Tag {fecha_texto} no existe"))
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
                progreso_base = 0.1
                progreso_max = 0.95
                progreso = progreso_base + (progreso_max - progreso_base) * (i / total_tickets)
                self.after(0, lambda p=progreso: self.actualizar_progreso(p))

                connection_id = ticket.get("connectionId")
                connection_data = obtener_connection(connection_id) if connection_id else None
                connection_name = connection_data.get("name") if connection_data else None
                ticket_id = ticket["id"]

                if connection_name == CONNECTION_WHATSAPP:
                    nombre_contacto = ticket["contact"]["name"]
                    if ENVIAR_INMEDIATO:
                        enviar_nota_rapida(ticket_id, "NOT0", 0, None, nombre_contacto)
                    enviar_nota_rapida(ticket_id, "NOT1", DIAS_A_SUMAR_PROGRAMADO1, HORA_ENVIO_PROGRAMADO1, nombre_contacto)
                    enviar_nota_rapida(ticket_id, "NOT2", DIAS_A_SUMAR_PROGRAMADO2, HORA_ENVIO_PROGRAMADO2, nombre_contacto)
                    transferir_ticket(ticket_id, queue_id_destino, USER_ID_DESTINO)

                elif connection_name == CONNECTION_BUSINESS:
                    fecha_entrega = datetime.now() + timedelta(days=DIAS_A_SUMAR_TAG)
                    fecha_entrega_texto = fecha_entrega.strftime("%d/%m")

                    if ENVIAR_INMEDIATO:
                        enviar_plantilla_waba(ticket_id, "NOT0", [fecha_entrega_texto], 0, None)
                    enviar_plantilla_waba(ticket_id, "NOT1", None, DIAS_A_SUMAR_PROGRAMADO1+1, HORA_ENVIO_PROGRAMADO1)
                    enviar_plantilla_waba(ticket_id, "NOT2", None, DIAS_A_SUMAR_PROGRAMADO2, HORA_ENVIO_PROGRAMADO2)
                    transferir_ticket(ticket_id, queue_id_destino, USER_ID_DESTINO)

            self.after(0, lambda: self.actualizar_progreso(1.0))
            self._fin_ejecucion()

        except Exception as e:
            self.after(0, lambda: self.mostrar_error(f"Error: {str(e)}"))
            self._fin_ejecucion()

    def _fin_ejecucion(self):
        self.ejecutando = False
        self.btn_ejecutar.configure(state="normal", text="EJECUTAR ENVIO")


def obtener_configuracion() -> dict:
    return {
        "TOKEN": TOKEN,
        "DIAS_A_SUMAR_TAG": DIAS_A_SUMAR_TAG,
        "LIMITE_TICKETS": LIMITE_TICKETS,
        "ENVIAR_INMEDIATO": ENVIAR_INMEDIATO
    }


def main():
    app = ConfigApp()
    app.mainloop()


if __name__ == "__main__":
    main()
