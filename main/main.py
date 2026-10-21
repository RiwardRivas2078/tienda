import reflex as rx
import urllib.parse
import base64
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from functools import lru_cache
import urllib3

# Desactivar advertencias de SSL para el BCV
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- SCRAPING BCV CON TU CÓDIGO ---
@lru_cache(maxsize=1)
def obtener_tasa_bcv():
    try:
        response = requests.get("https://www.bcv.org.ve/", verify=False, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        tasa_raw = soup.find("div", {"id": "dolar"}).find("strong").text.strip()
        return float(tasa_raw.replace('.', '').replace(',', '.'))
    except Exception:
        return 36.50

TASA_ACTUAL = obtener_tasa_bcv()
FECHA_ACTUAL = datetime.now().strftime("%d/%m/%Y")

# --- ESTADO ---
class State(rx.State):
    texto_cliente: str = ""
    logo_subido: list[str] = []
    carrito: list[dict] = []
    TASA_BCV: float = TASA_ACTUAL
    FECHA: str = FECHA_ACTUAL

    def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            upload_data = file.file.read()
            encoded = base64.b64encode(upload_data).decode("utf-8")
            self.logo_subido = [f"data:image/png;base64,{encoded}"]

    def limpiar_logo(self):
        self.logo_subido = []

    def agregar_al_carrito(self, nombre: str, precio: float):
        for item in self.carrito:
            if item["nombre"] == nombre:
                item["cantidad"] += 1
                return
        self.carrito.append({"nombre": nombre, "precio": precio, "cantidad": 1})

    def quitar_del_carrito(self, index: int):
        self.carrito.pop(index)

    def vaciar_carrito(self):
        self.carrito = []

    def sumar_cantidad(self, index: int):
        self.carrito[index]["cantidad"] += 1

    def restar_cantidad(self, index: int):
        if self.carrito[index]["cantidad"] > 1:
            self.carrito[index]["cantidad"] -= 1
        else:
            self.quitar_del_carrito(index)

    @rx.var
    def total_usd(self) -> float:
        return sum(item["precio"] * item["cantidad"] for item in self.carrito)

    @rx.var
    def total_bs(self) -> str:
        return f"Bs. {(self.total_usd * self.TASA_BCV):,.2f}"

    @rx.var
    def link_whatsapp_cotizacion(self) -> str:
        if not self.carrito:
            return "https://wa.me/584242446795?text=Hola,%20quiero%20cotizar."
        mensaje = "Hola SubliCaracas, quiero cotizar lo siguiente:\n"
        for item in self.carrito:
            subtotal = item['precio'] * item['cantidad']
            mensaje += f"- {item['nombre']} x{item['cantidad']} (${subtotal:.2f})\n"
        mensaje += f"\nTotal: ${self.total_usd:.2f} / {self.total_bs}"
        return f"https://wa.me/584242446795?text={urllib.parse.quote(mensaje)}"

WHATSAPP_NUMERO = "584242446795"

# --- COMPONENTES ---

def banner_carga() -> rx.Component:
    # Banner elegante para cuando Render está despertando
    return rx.box(
        rx.hstack(
            rx.spinner(size="2", color="#2563EB"),
            rx.text("Conectando con el servidor (puede tardar unos segundos)...", size="2", color="#1E293B", weight="medium"),
            spacing="3", align="center", justify="center"
        ),
        width="100%", padding="0.8em", bg="#EFF6FF", border_bottom="1px solid #BFDBFE", position="sticky", top="0", z_index="99999"
    )

def ticker_tasa() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(f"Tasa Oficial BCV: {State.TASA_BCV:.2f} Bs/$", size="1", color="white", weight="bold"),
            rx.text(f"| Actualizado el: {State.FECHA}", size="1", color="rgba(255,255,255,0.7)"),
            spacing="2", justify="center", width="100%"
        ),
        bg="#0F172A", padding="0.6em", width="100%"
    )

def navbar() -> rx.Component:
    return rx.vstack(
        ticker_tasa(),
        rx.box(
            rx.container(
                rx.flex(
                    rx.hstack(
                        rx.icon(tag="hexagon", color="#2563EB", size=24), # Icono más tecnológico
                        rx.heading("SubliCaracas", size="5", weight="bold", color="#0F172A", letter_spacing="-0.05em"),
                        align="center",
                    ),
                    rx.flex(
                        rx.link("Catálogo", href="#catalogo", color="#64748B", weight="medium", _hover={"color": "#2563EB"}),
                        rx.link("Galería", href="#galeria", color="#64748B", weight="medium", _hover={"color": "#2563EB"}),
                        rx.link("Cotizar Diseño", href="#personalizar", color="#64748B", weight="medium", _hover={"color": "#2563EB"}),
                        spacing="6", direction=rx.breakpoints(initial="row", sm="row"), justify="center",
                    ),
                    direction=rx.breakpoints(initial="column", md="row"),
                    justify="between", align="center", width="100%", gap="1em", padding_y="1.2em"
                ),
                size="4"
            ),
            width="100%", bg="rgba(255, 255, 255, 0.9)", backdrop_filter="blur(12px)", border_bottom="1px solid #F1F5F9", position="sticky", top="0", z_index="1000",
        ),
        spacing="0", width="100%"
    )

def tarjeta_producto(nombre: str, precio: float, imagen: str, desc: str) -> rx.Component:
    precio_bs = f"Bs. {(precio * State.TASA_BCV):,.2f}"
    return rx.box(
        rx.vstack(
            rx.box(
                rx.image(src=imagen, width="100%", height="260px", object_fit="cover"),
                rx.badge(f"${precio:.2f}", color_scheme="blue", variant="solid", size="1", position="absolute", top="12px", right="12px", border_radius="full"),
                position="relative", width="100%",
            ),
            rx.vstack(
                rx.heading(nombre, size="3", weight="bold", color="#0F172A"),
                rx.text(desc, size="1", color="#64748B", min_height="30px"),
                rx.hstack(
                    rx.text(f"Bs. {precio_bs}", color="#94A3B8", size="1"),
                    rx.spacer(),
                    rx.button(
                        rx.icon(tag="plus", size=14), 
                        on_click=lambda: State.agregar_al_carrito(nombre, precio),
                        bg="#F1F5F9", color="#0F172A", border_radius="full", size="1", 
                        _hover={"bg": "#2563EB", "color": "white"}
                    ),
                ),
                align_items="start", width="100%", padding="1.2em",
            ),
            spacing="0", width="100%", bg="white",
        ),
        border="1px solid #F1F5F9", border_radius="12px", overflow="hidden", width="100%",
        _hover={"box_shadow": "0 10px 25px -5px rgba(0, 0, 0, 0.05)", "transform": "translateY(-2px)", "transition": "0.3s"}
    )

def galeria_trabajos() -> rx.Component:
    productos = [
        {"nombre": "Pijama Navideña", "precio": 18.00, "foto": "/pijama1.jpeg", "desc": "Diseño exclusivo."},
        {"nombre": "Pijama Ositos", "precio": 20.00, "foto": "/pijama2.jpeg", "desc": "Tela suave."},
        {"nombre": "Pijama Grinch", "precio": 22.00, "foto": "/pijama3.jpeg", "desc": "Divertida."},
        {"nombre": "Pijama Rosada", "precio": 18.00, "foto": "/pijama4.jpeg", "desc": "Relajado."},
        {"nombre": "Pijama Cuadros", "precio": 20.00, "foto": "/pijama5.jpeg", "desc": "Clásico."},
    ]
    return rx.vstack(
        rx.heading("Colección de Pijamas", size="6", weight="bold", color="#0F172A", letter_spacing="-0.02em"),
        rx.grid(
            *[tarjeta_producto(p["nombre"], p["precio"], p["foto"], p["desc"]) for p in productos],
            columns=rx.breakpoints(initial="2", sm="2", md="3", lg="5"),
            spacing="4", width="100%", margin_top="2em",
        ),
        padding="4em 2em", width="100%", align="center", bg="#FFFFFF", id="galeria"
    )

def seccion_personalizador() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.vstack(
                rx.heading("Cotiza tu diseño personalizado", size="6", weight="bold", color="#0F172A", letter_spacing="-0.02em"),
                rx.text("Sube tu logo y cuéntanos qué necesitas. Te enviaremos una muestra por WhatsApp.", color="#64748B", size="3", line_height="1.6"),
                rx.divider(margin_y="1.5em", border_color="#F1F5F9"),
                rx.text("Garantía SubliCaracas: Si no te gusta el diseño, no pagas nada.", color="#2563EB", weight="bold", size="2"),
                align="start",
                width=rx.breakpoints(initial="100%", md="50%"),
                padding_right=rx.breakpoints(initial="0", md="2em"),
                margin_bottom=rx.breakpoints(initial="2em", md="0"),
            ),
            rx.vstack(
                rx.text("1. Sube tu logo (PNG)", weight="bold", size="2", color="#0F172A"),
                rx.upload(
                    rx.vstack(rx.icon(tag="upload-cloud", size=32, color="#2563EB"), rx.text("Haz clic o arrastra tu archivo", size="2", color="#64748B"), align="center"),
                    id="logo_upload", border="2px dashed #CBD5E1", padding="2.5em", border_radius="12px", background="#F8FAFC",
                    on_drop=State.handle_upload(rx.upload_files(upload_id="logo_upload")), width="100%",
                    _hover={"border_color": "#2563EB", "background": "#EFF6FF"}
                ),
                rx.cond(
                    State.logo_subido.length() > 0,
                    rx.button("Quitar imagen", on_click=State.limpiar_logo, size="1", variant="soft", color_scheme="red", margin_top="0.5em", width="100%")
                ),
                rx.text("2. Describe tu idea o escribe el texto", weight="bold", size="2", color="#0F172A", margin_top="1.5em"),
                rx.input(placeholder="Ej: Gorra con el logo de mi empresa...", value=State.texto_cliente, on_change=State.set_texto_cliente, width="100%", size="3", margin_bottom="1.5em", border_radius="8px"),
                rx.button(
                    "Solicitar Cotización por WhatsApp", on_click=lambda: State.agregar_al_carrito("Diseño Personalizado", 12.00),
                    bg="#2563EB", color="white", width="100%", size="3", border_radius="8px", _hover={"bg": "#1D4ED8"}
                ),
                width=rx.breakpoints(initial="100%", md="50%"),
                align_items="start",
            ),
            direction=rx.breakpoints(initial="column", md="row"),
            width="100%", align="center", spacing="6", padding=rx.breakpoints(initial="2em 1em", md="4em")
        ),
        background="#FFFFFF", border="1px solid #F1F5F9", border_radius="16px", width="100%", max_width="1000px", margin="0 auto",
        box_shadow="0 4px 6px -1px rgba(0,0,0,0.02)"
    )

def footer() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="instagram", size=24, color="#64748B", cursor="pointer", _hover={"color": "#2563EB"}),
                rx.icon(tag="message-circle", size=24, color="#64748B", cursor="pointer", _hover={"color": "#2563EB"}),
                rx.icon(tag="music", size=24, color="#64748B", cursor="pointer", _hover={"color": "#2563EB"}),
                spacing="6", margin_bottom="1em"
            ),
            rx.text("© 2024 SubliCaracas. Tecnología y diseño venezolano.", color="#94A3B8", size="1"),
            align="center", padding="3em", width="100%", bg="#FFFFFF", border_top="1px solid #F1F5F9"
        ),
        width="100%"
    )

# --- BOTÓN FLOTANTE DE WHATSAPP (TECNOLÓGICO) ---
def boton_flotante_whatsapp() -> rx.Component:
    return rx.link(
        rx.box(
            rx.icon(tag="message-circle", size=32, color="white"),
            bg="#25D366",
            padding="1em",
            border_radius="full",
            box_shadow="0 10px 25px rgba(37, 211, 102, 0.5)",
            position="fixed",
            bottom="20px",
            right="20px",
            z_index="9999",
            cursor="pointer",
            _hover={"transform": "scale(1.1)", "transition": "all 0.3s ease", "bg": "#128C7E"},
            animation="pulse 2s infinite"
        ),
        href="https://wa.me/584242446795?text=Hola,%20quiero%20más%20información",
        is_external=True
    )

def cotizador_flotante() -> rx.Component:
    return rx.cond(
        State.carrito.length() > 0,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("Tu Cotización", size="4", weight="bold", color="#0F172A"),
                    rx.spacer(),
                    rx.text(f"${State.total_usd:.2f}", color="#2563EB", weight="bold", size="4")
                ),
                rx.text(f"Total en Bs: {State.total_bs}", color="#64748B", size="2"),
                rx.divider(margin_y="0.5em", border_color="#F1F5F9"),
                rx.vstack(
                    rx.foreach(
                        State.carrito, 
                        lambda item, i: rx.hstack(
                            rx.text(f"{item['nombre']} (x{item['cantidad']})", size="2", weight="medium", color="#0F172A"),
                            rx.spacer(),
                            rx.icon(tag="minus", size=16, cursor="pointer", on_click=lambda: State.restar_cantidad(i), color="#94A3B8", _hover={"color": "#EF4444"}),
                            rx.text(item['cantidad'], size="2", weight="bold"),
                            rx.icon(tag="plus", size=16, cursor="pointer", on_click=lambda: State.sumar_cantidad(i), color="#94A3B8", _hover={"color": "#10B981"}),
                            rx.icon(tag="trash-2", size=16, color="#EF4444", cursor="pointer", on_click=lambda: State.quitar_del_carrito(i), margin_left="0.5em"),
                            width="100%", align="center", spacing="2"
                        )
                    ),
                    max_height="180px", overflow_y="auto", width="100%"
                ),
                rx.button("Vaciar Carrito", on_click=State.vaciar_carrito, size="1", variant="ghost", color_scheme="red", width="100%", margin_top="0.5em"),
                rx.link(rx.button("Pedir por WhatsApp", bg="#25D366", color="white", width="100%", margin_top="0.5em", size="3", border_radius="8px"), href=State.link_whatsapp_cotizacion, is_external=True, width="100%"),
                padding="1.5em", width="100%"
            ),
            position="fixed", bottom="90px", right="20px", width="calc(100% - 40px)", max_width="320px", background="white", border_radius="12px", border="1px solid #E2E8F0", z_index="9998", box_shadow="0 10px 25px -5px rgba(0,0,0,0.1)"
        )
    )

def index() -> rx.Component:
    return rx.vstack(
        banner_carga(), # Agregado para el aviso de "Render despertando"
        navbar(),
        boton_flotante_whatsapp(),
        cotizador_flotante(),
        
        # --- HERO SECTION ---
        rx.box(
            rx.image(
                src="https://images.unsplash.com/photo-1523381210434-271e8be1f52b?q=80&w=1920&auto=format&fit=crop", 
                width="100%", height="100%", object_fit="cover", position="absolute", top="0", left="0", z_index="0"
            ),
            rx.box(position="absolute", top="0", left="0", width="100%", height="100%", background="linear-gradient(to right, rgba(15,23,42,0.9) 0%, rgba(15,23,42,0.4) 100%)", z_index="1"),
            
            rx.vstack(
                rx.badge("TEXTILES Y SUBLIMACIÓN", color_scheme="blue", variant="solid", size="1"),
                rx.heading("Tecnología en cada diseño.", size=rx.breakpoints(initial="7", sm="8", md="9"), weight="bold", text_align="left", color="white", line_height="1.1", letter_spacing="-0.03em"),
                rx.text("Tazas, gorras y franelas de alta gama en Caracas.", color="rgba(255,255,255,0.8)", size=rx.breakpoints(initial="3", sm="4", md="4")),
                rx.button("Ver Catálogo", on_click=rx.call_script("document.getElementById('catalogo').scrollIntoView({behavior: 'smooth'})"), size="3", bg="#2563EB", color="white", border_radius="8px", margin_top="1.5em", _hover={"bg": "#1D4ED8"}),
                align="start", padding=rx.breakpoints(initial="4em 2em", sm="6em 3em", md="8em 5em"), width="100%", max_width="1200px", z_index="2",
            ),
            position="relative", width="100%", min_height="65vh", display="flex", align_items="center", justify_content="center", overflow="hidden"
        ),
        
        # CATÁLOGO
        rx.vstack(
            rx.heading("Catálogo Destacado", size="6", weight="bold", color="#0F172A", letter_spacing="-0.02em"),
            rx.grid(
                tarjeta_producto("Taza Cerámica", 8.00, "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Acabado brillante."),
                tarjeta_producto("Gorra Premium", 12.00, "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Malla transpirable."),
                tarjeta_producto("Franela Algodón", 15.00, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Corte moderno."),
                columns=rx.breakpoints(initial="2", sm="2", md="3"),
                spacing="4", width="100%", margin_top="2em",
            ),
            padding="4em 2em", width="100%", align="center", bg="#FFFFFF", id="catalogo"
        ),

        galeria_trabajos(),

        rx.box(
            seccion_personalizador(),
            width="100%", padding="4em 2em", bg="#F8FAFC", id="personalizar"
        ),
        
        footer(),
        
        bg="#FFFFFF", min_height="100vh", align="center", width="100%", spacing="0",
    )

app = rx.App(style={"font_family": "'Inter', system-ui, sans-serif"})
app.add_page(index)