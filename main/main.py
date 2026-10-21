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

# --- SCRAPING BCV ---
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

# --- COLORES TECH ---
BG_DARK = "#09090B"       # Fondo principal (casi negro)
CARD_BG = "#18181B"       # Fondo de tarjetas
TEXT_WHITE = "#FAFAFA"    # Texto principal
TEXT_GRAY = "#A1A1AA"     # Texto secundario
ACCENT_BLUE = "#3B82F6"   # Azul eléctrico
ACCENT_GREEN = "#25D366"  # Verde WhatsApp

# --- COMPONENTES ---

def ticker_tasa() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon(tag="activity", size=14, color=ACCENT_GREEN),
            rx.text(f"TASA BCV: {State.TASA_BCV:.2f} Bs/$", size="1", color=TEXT_WHITE, weight="bold", letter_spacing="1px"),
            rx.text(f"| {State.FECHA}", size="1", color=TEXT_GRAY),
            spacing="2", justify="center", width="100%"
        ),
        bg="#000000", padding="0.5em", width="100%", border_bottom="1px solid #27272A"
    )

def navbar() -> rx.Component:
    return rx.vstack(
        ticker_tasa(),
        rx.box(
            rx.container(
                rx.flex(
                    rx.hstack(
                        rx.icon(tag="zap", color=ACCENT_BLUE, size=24),
                        rx.heading("SubliCaracas", size="5", weight="bold", color=TEXT_WHITE, letter_spacing="-0.05em"),
                        align="center",
                    ),
                    rx.flex(
                        rx.link("Catálogo", href="#catalogo", color=TEXT_GRAY, weight="medium", _hover={"color": TEXT_WHITE}),
                        rx.link("Personalizar", href="#personalizar", color=TEXT_GRAY, weight="medium", _hover={"color": TEXT_WHITE}),
                        spacing="6", direction=rx.breakpoints(initial="row", sm="row"), justify="center",
                    ),
                    direction=rx.breakpoints(initial="column", md="row"),
                    justify="between", align="center", width="100%", gap="1em", padding_y="1.2em"
                ),
                size="4"
            ),
            width="100%", bg="rgba(9, 9, 11, 0.8)", backdrop_filter="blur(12px)", border_bottom="1px solid #27272A", position="sticky", top="0", z_index="1000",
        ),
        spacing="0", width="100%"
    )

def tarjeta_producto(nombre: str, precio: float, imagen: str, desc: str) -> rx.Component:
    precio_bs = f"Bs. {(precio * State.TASA_BCV):,.2f}"
    return rx.box(
        rx.vstack(
            rx.box(
                rx.image(src=imagen, width="100%", height="240px", object_fit="cover", border_radius="8px 8px 0 0"),
                rx.badge(f"${precio:.2f}", color_scheme="blue", variant="solid", size="1", position="absolute", top="12px", right="12px", border_radius="full", box_shadow="0 0 10px rgba(59, 130, 246, 0.5)"),
                position="relative", width="100%",
            ),
            rx.vstack(
                rx.heading(nombre, size="3", weight="bold", color=TEXT_WHITE),
                rx.text(desc, size="1", color=TEXT_GRAY, min_height="30px"),
                rx.hstack(
                    rx.text(f"Bs. {precio_bs}", color=TEXT_GRAY, size="1"),
                    rx.spacer(),
                    rx.button(
                        rx.icon(tag="plus", size=14), 
                        on_click=lambda: State.agregar_al_carrito(nombre, precio),
                        bg="#27272A", color=TEXT_WHITE, border_radius="full", size="1", 
                        _hover={"bg": ACCENT_BLUE, "color": "white", "box_shadow": "0 0 10px rgba(59, 130, 246, 0.5)"}
                    ),
                ),
                align_items="start", width="100%", padding="1.2em",
            ),
            spacing="0", width="100%", bg=CARD_BG, border_radius="12px",
        ),
        border="1px solid #27272A", border_radius="12px", overflow="hidden", width="100%",
        _hover={"border_color": ACCENT_BLUE, "box_shadow": "0 0 20px rgba(59, 130, 246, 0.1)", "transform": "translateY(-4px)", "transition": "0.3s"}
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
        rx.heading("Colección de Pijamas", size="6", weight="bold", color=TEXT_WHITE, letter_spacing="-0.02em"),
        rx.grid(
            *[tarjeta_producto(p["nombre"], p["precio"], p["foto"], p["desc"]) for p in productos],
            columns=rx.breakpoints(initial="1", sm="2", md="3", lg="5"),
            spacing="4", width="100%", margin_top="2em",
        ),
        padding="4em 2em", width="100%", align="center", bg=BG_DARK, id="galeria"
    )

def seccion_personalizador() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.vstack(
                rx.badge("HERRAMIENTA DE DISEÑO", color_scheme="blue", variant="soft", size="1", margin_bottom="1em"),
                rx.heading("Sube tu diseño, nosotros lo hacemos realidad.", size="6", weight="bold", color=TEXT_WHITE, letter_spacing="-0.02em"),
                rx.text("Envía tu logo o idea. Te enviaremos una muestra real por WhatsApp antes de que pagues.", color=TEXT_GRAY, size="3", line_height="1.6"),
                rx.divider(margin_y="1.5em", border_color="#27272A"),
                rx.hstack(
                    rx.icon(tag="shield-check", color=ACCENT_GREEN, size=20),
                    rx.text("Garantía: Si no te gusta el diseño, no pagas nada.", color=TEXT_WHITE, weight="medium", size="2"),
                    spacing="2", align="center"
                ),
                align="start",
                width=rx.breakpoints(initial="100%", md="50%"),
                padding_right=rx.breakpoints(initial="0", md="2em"),
                margin_bottom=rx.breakpoints(initial="2em", md="0"),
            ),
            rx.vstack(
                rx.text("1. Sube tu logo (PNG)", weight="bold", size="2", color=TEXT_WHITE),
                rx.upload(
                    rx.vstack(rx.icon(tag="upload-cloud", size=32, color=ACCENT_BLUE), rx.text("Haz clic o arrastra tu archivo", size="2", color=TEXT_GRAY), align="center"),
                    id="logo_upload", border="2px dashed #3F3F46", padding="2.5em", border_radius="12px", background="#18181B",
                    on_drop=State.handle_upload(rx.upload_files(upload_id="logo_upload")), width="100%",
                    _hover={"border_color": ACCENT_BLUE, "background": "#27272A"}
                ),
                rx.cond(
                    State.logo_subido.length() > 0,
                    rx.button("Quitar imagen", on_click=State.limpiar_logo, size="1", variant="soft", color_scheme="red", margin_top="0.5em", width="100%")
                ),
                rx.text("2. Describe tu idea", weight="bold", size="2", color=TEXT_WHITE, margin_top="1.5em"),
                rx.input(placeholder="Ej: Gorra con el logo de mi empresa...", value=State.texto_cliente, on_change=State.set_texto_cliente, width="100%", size="3", margin_bottom="1.5em", border_radius="8px", bg="#18181B", border="1px solid #3F3F46", color=TEXT_WHITE),
                
                # BOTÓN DE WHATSAPP TIPO TECNOLÓGICO
                rx.link(
                    rx.button(
                        rx.icon(tag="message-circle", size=20),
                        "Solicitar Cotización por WhatsApp", 
                        bg=ACCENT_GREEN, color="black", width="100%", size="3", border_radius="8px", weight="bold",
                        _hover={"bg": "#1EA952", "box_shadow": "0 0 15px rgba(37, 211, 102, 0.4)"}
                    ),
                    href="https://wa.me/584242446795?text=Hola,%20quiero%20cotizar%20un%20diseño%20personalizado", 
                    is_external=True, width="100%"
                ),
                width=rx.breakpoints(initial="100%", md="50%"),
                align_items="start",
            ),
            direction=rx.breakpoints(initial="column", md="row"),
            width="100%", align="center", spacing="6", padding=rx.breakpoints(initial="2em 1em", md="4em")
        ),
        background=CARD_BG, border="1px solid #27272A", border_radius="16px", width="100%", max_width="1000px", margin="0 auto",
        box_shadow="0 4px 20px -1px rgba(0,0,0,0.5)"
    )

def footer() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="instagram", size=24, color=TEXT_GRAY, cursor="pointer", _hover={"color": ACCENT_BLUE}),
                rx.icon(tag="message-circle", size=24, color=TEXT_GRAY, cursor="pointer", _hover={"color": ACCENT_GREEN}),
                rx.icon(tag="music", size=24, color=TEXT_GRAY, cursor="pointer", _hover={"color": ACCENT_BLUE}),
                spacing="6", margin_bottom="1em"
            ),
            rx.text("© 2024 SubliCaracas. Impulsado por tecnología.", color="#52525B", size="1"),
            align="center", padding="3em", width="100%", bg="#000000", border_top="1px solid #27272A"
        ),
        width="100%"
    )

# --- BOTÓN FLOTANTE DE WHATSAPP (ESTILO NEÓN) ---
def boton_flotante_whatsapp() -> rx.Component:
    return rx.link(
        rx.box(
            rx.icon(tag="message-circle", size=35, color="black"),
            bg=ACCENT_GREEN,
            padding="1em",
            border_radius="full",
            box_shadow="0 0 20px rgba(37, 211, 102, 0.6)",
            position="fixed",
            bottom="20px",
            right="20px",
            z_index="9999",
            cursor="pointer",
            _hover={"transform": "scale(1.1)", "transition": "all 0.3s ease", "box_shadow": "0 0 30px rgba(37, 211, 102, 0.8)"},
            animation="pulse 2s infinite"
        ),
        href="https://wa.me/584242446795?text=Hola,%20quiero%20información",
        is_external=True
    )

def index() -> rx.Component:
    return rx.vstack(
        navbar(),
        boton_flotante_whatsapp(),
        
        # --- HERO SECTION (TECH OSCURO) ---
        rx.box(
            # Gradiente radial sutil en el fondo
            rx.box(position="absolute", top="0", left="0", width="100%", height="100%", background="radial-gradient(circle at 50% 0%, #1E1B4B 0%, #09090B 70%)", z_index="0"),
            
            rx.vstack(
                rx.badge("EL FUTURO DEL DISEÑO TEXTIL", color_scheme="blue", variant="solid", size="1", padding="0.5em 1em", border_radius="full"),
                rx.heading("Tecnología en cada diseño.", size=rx.breakpoints(initial="8", sm="9", md="9"), weight="bold", text_align="center", color=TEXT_WHITE, line_height="1.1", letter_spacing="-0.05em", margin_top="0.5em"),
                rx.text("Sublimación de alta gama. Tazas, gorras y franelas para quienes buscan la perfección.", color=TEXT_GRAY, size=rx.breakpoints(initial="3", sm="4", md="4"), text_align="center", max_width="600px", margin_top="1em"),
                rx.hstack(
                    rx.button("Explorar Catálogo", on_click=rx.call_script("document.getElementById('catalogo').scrollIntoView({behavior: 'smooth'})"), size="3", bg=TEXT_WHITE, color="black", border_radius="8px", weight="bold", _hover={"bg": "#D4D4D8"}),
                    rx.button("Personalizar", on_click=rx.call_script("document.getElementById('personalizar').scrollIntoView({behavior: 'smooth'})"), size="3", variant="outline", color=TEXT_WHITE, border_color="#3F3F46", border_radius="8px", _hover={"bg": "#18181B"}),
                    spacing="4", margin_top="2em"
                ),
                align="center", padding=rx.breakpoints(initial="6em 2em", sm="8em 2em", md="10em 2em"), width="100%", z_index="1",
            ),
            position="relative", width="100%", min_height="70vh", display="flex", align_items="center", justify_content="center", overflow="hidden", border_bottom="1px solid #27272A"
        ),
        
        # CATÁLOGO
        rx.vstack(
            rx.heading("Catálogo Destacado", size="6", weight="bold", color=TEXT_WHITE, letter_spacing="-0.02em"),
            rx.grid(
                tarjeta_producto("Taza Cerámica", 8.00, "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Acabado brillante."),
                tarjeta_producto("Gorra Premium", 12.00, "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Malla transpirable."),
                tarjeta_producto("Franela Algodón", 15.00, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Corte moderno."),
                columns=rx.breakpoints(initial="1", sm="2", md="3"),
                spacing="6", width="100%", margin_top="2em",
            ),
            padding="6em 2em", width="100%", align="center", bg=BG_DARK, id="catalogo"
        ),

        galeria_trabajos(),

        rx.box(
            seccion_personalizador(),
            width="100%", padding="6em 2em", bg=BG_DARK, id="personalizar"
        ),
        
        footer(),
        
        bg=BG_DARK, min_height="100vh", align="center", width="100%", spacing="0",
    )

app = rx.App(style={"font_family": "'Inter', system-ui, sans-serif"})
app.add_page(index)