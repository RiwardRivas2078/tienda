import reflex as rx
import urllib.parse
import base64
import requests
from bs4 import BeautifulSoup
from functools import lru_cache
import urllib3

# Desactivar advertencias de SSL para el BCV
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- SCRAPING BCV USANDO TU CÓDIGO (con caché) ---
@lru_cache(maxsize=1)
def obtener_tasa_bcv():
    try:
        response = requests.get("https://www.bcv.org.ve/", verify=False, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        tasa_raw = soup.find("div", {"id": "dolar"}).find("strong").text.strip()
        return float(tasa_raw.replace('.', '').replace(',', '.'))
    except Exception as e:
        print(f"Error al obtener tasa: {e}")
        return 36.50 # Respaldo

# --- ESTADO ---
class State(rx.State):
    texto_cliente: str = ""
    logo_subido: list[str] = []
    carrito: list[dict] = []
    TASA_BCV: float = obtener_tasa_bcv()
    
    # Para el selector de producto en el personalizador
    producto_actual: str = "Gorra"

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

def navbar() -> rx.Component:
    return rx.box(
        rx.container(
            rx.flex(
                rx.hstack(
                    rx.icon(tag="sparkles", color="#2C2C2C", size=24),
                    rx.heading("SubliCaracas", size="5", weight="bold", color="#2C2C2C"),
                    align="center",
                ),
                rx.flex(
                    rx.link("Catálogo", href="#catalogo", color="#6B7280", weight="medium", _hover={"color": "#D96B43"}),
                    rx.link("Galería", href="#galeria", color="#6B7280", weight="medium", _hover={"color": "#D96B43"}),
                    rx.link("Personalizar", href="#personalizar", color="#6B7280", weight="medium", _hover={"color": "#D96B43"}),
                    rx.color_mode.button(), 
                    spacing="4", direction=rx.breakpoints(initial="row", sm="row"), justify="center",
                ),
                direction=rx.breakpoints(initial="column", md="row"),
                justify="between", align="center", width="100%", gap="1em", padding_y="1em"
            ),
            size="4"
        ),
        width="100%", bg="#F9F6F0", border_bottom="1px solid #E5E0D8", position="sticky", top="0", z_index="1000",
    )

def tarjeta_producto(nombre: str, precio: float, imagen: str, desc: str) -> rx.Component:
    precio_bs = f"Bs. {(precio * State.TASA_BCV):,.2f}"
    return rx.box(
        rx.vstack(
            rx.box(
                rx.image(src=imagen, width="100%", height="200px", object_fit="cover"),
                rx.badge(f"${precio:.2f}", color_scheme="orange", variant="solid", size="2", position="absolute", bottom="10px", right="10px"),
                position="relative", width="100%",
            ),
            rx.vstack(
                rx.heading(nombre, size="3", weight="bold", color="#2C2C2C"),
                rx.text(desc, size="1", color="#6B7280", min_height="30px"),
                rx.text(f"Bs. {precio_bs}", color="#9CA3AF", size="1"),
                rx.button(
                    rx.icon(tag="plus", size=14), "Agregar", 
                    on_click=lambda: State.agregar_al_carrito(nombre, precio),
                    bg="#2C2C2C", color="white", width="100%", border_radius="6px", size="2", _hover={"bg": "#D96B43"}
                ),
                align_items="start", width="100%", padding="1em",
            ),
            spacing="0", width="100%", bg="white",
        ),
        border="1px solid #E5E0D8", border_radius="12px", overflow="hidden", width="100%",
        _hover={"box_shadow": "0 10px 15px -3px rgba(0,0,0,0.1)", "transform": "translateY(-2px)", "transition": "0.3s"}
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
        rx.heading("Nuestras Creaciones", size="5", weight="bold", color="#2C2C2C"),
        rx.grid(
            *[tarjeta_producto(p["nombre"], p["precio"], p["foto"], p["desc"]) for p in productos],
            columns=rx.breakpoints(initial="1", sm="2", md="3", lg="5"),
            spacing="4", width="100%", margin_top="1em",
        ),
        padding="4em 2em", width="100%", align="center", bg="#F9F6F0", id="galeria"
    )

# --- NUEVO PERSONALIZADOR ---
def seccion_personalizador() -> rx.Component:
    # Lógica para cambiar la imagen según el producto seleccionado
    imagen_mockup = rx.cond(
        State.producto_actual == "Gorra",
        "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
        rx.cond(
            State.producto_actual == "Taza",
            "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80" # Franela
        )
    )

    return rx.box(
        rx.flex(
            # Lado Izquierdo: El Mockup (Previsualización)
            rx.vstack(
                # Selector de producto
                rx.hstack(
                    rx.button("Gorra", on_click=lambda: State.set_producto_actual("Gorra"), size="1", variant=rx.cond(State.producto_actual == "Gorra", "solid", "outline"), color_scheme="orange"),
                    rx.button("Taza", on_click=lambda: State.set_producto_actual("Taza"), size="1", variant=rx.cond(State.producto_actual == "Taza", "solid", "outline"), color_scheme="orange"),
                    rx.button("Franela", on_click=lambda: State.set_producto_actual("Franela"), size="1", variant=rx.cond(State.producto_actual == "Franela", "solid", "outline"), color_scheme="orange"),
                    spacing="2", justify="center", width="100%", margin_bottom="1em"
                ),
                # Área de la imagen con el logo
                rx.box(
                    rx.image(src=imagen_mockup, width="100%", border_radius="8px"),
                    rx.center(
                        rx.vstack(
                            rx.cond(
                                State.logo_subido.length() > 0,
                                rx.image(
                                    src=State.logo_subido[0], 
                                    width="100px", 
                                    mix_blend_mode="multiply", 
                                    # Sombra para darle realismo
                                    filter="drop-shadow(2px 4px 6px rgba(0,0,0,0.4))"
                                )
                            ),
                            rx.cond(
                                State.texto_cliente != "",
                                rx.text(State.texto_cliente, font_size="16px", font_weight="bold", color="#1e293b", text_align="center", text_shadow="1px 1px 2px white")
                            ),
                            align="center",
                            padding_top="5%"
                        ),
                        position="absolute", top="0", left="0", width="100%", height="100%"
                    ),
                    position="relative", width="100%", max_width="400px", margin="0 auto"
                ),
                rx.cond(
                    State.logo_subido.length() > 0,
                    rx.button("Quitar logo", on_click=State.limpiar_logo, size="1", variant="soft", color_scheme="red", margin_top="1em", width="100%")
                ),
                width=rx.breakpoints(initial="100%", md="50%"),
                margin_bottom=rx.breakpoints(initial="2em", md="0"),
            ),
            
            # Lado Derecho: Controles tipo App
            rx.vstack(
                rx.heading("Simulador de Diseño", size="5", weight="bold", color="#2C2C2C"),
                rx.text("Sube tu logo y escribe tu texto para ver cómo quedaría.", color="#6B7280", size="2"),
                rx.divider(margin_y="1em", border_color="#E5E0D8"),
                
                rx.text("1. Sube tu imagen (PNG transparente)", weight="bold", size="2", color="#2C2C2C"),
                rx.upload(
                    rx.vstack(rx.icon(tag="image", size=24, color="#D96B43"), rx.text("Arrastra tu diseño aquí", size="1", color="#6B7280"), align="center"),
                    id="logo_upload", border="2px dashed #D6D3D1", padding="2em", border_radius="8px", background="#FFFFFF",
                    on_drop=State.handle_upload(rx.upload_files(upload_id="logo_upload")), width="100%",
                    _hover={"border_color": "#D96B43", "background": "#FFF7ED"}
                ),
                rx.text("2. Escribe tu texto", weight="bold", size="2", color="#2C2C2C", margin_top="1.5em"),
                rx.input(placeholder="Ej: Feliz Cumpleaños...", value=State.texto_cliente, on_change=State.set_texto_cliente, width="100%", size="3", margin_bottom="1.5em"),
                rx.button(
                    "Agregar a cotización", on_click=lambda: State.agregar_al_carrito("Producto Personalizado", 12.00),
                    bg="#D96B43", color="white", width="100%", size="3", border_radius="6px", _hover={"bg": "#C25733"}
                ),
                width=rx.breakpoints(initial="100%", md="50%"),
                align_items="start",
                padding_left=rx.breakpoints(initial="0", md="2em"),
            ),
            direction=rx.breakpoints(initial="column", md="row"),
            width="100%", align="center", spacing="6", padding="2em"
        ),
        background="#FFFFFF", border_radius="16px", border="1px solid #E5E0D8", width="100%",
        box_shadow="0 4px 6px -1px rgba(0,0,0,0.05)"
    )

def cotizador_flotante() -> rx.Component:
    return rx.cond(
        State.carrito.length() > 0,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("Tu Cotización", size="4", weight="bold", color="#2C2C2C"),
                    rx.spacer(),
                    rx.text(f"${State.total_usd:.2f}", color="#D96B43", weight="bold", size="4")
                ),
                rx.text(f"Total en Bs: {State.total_bs}", color="#6B7280", size="2"),
                rx.divider(margin_y="0.5em"),
                rx.vstack(
                    rx.foreach(
                        State.carrito, 
                        lambda item, i: rx.hstack(
                            rx.text(f"{item['nombre']} (x{item['cantidad']})", size="2", weight="medium", color="#2C2C2C"),
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
                rx.link(rx.button("Pedir por WhatsApp", bg="#25D366", color="white", width="100%", margin_top="0.5em", size="3", border_radius="6px"), href=State.link_whatsapp_cotizacion, is_external=True, width="100%"),
                padding="1.5em", width="100%"
            ),
            position="fixed", bottom="15px", right="15px", width="calc(100% - 30px)", max_width="320px", background="white", border_radius="16px", z_index="9999", box_shadow="0 10px 25px -5px rgba(0,0,0,0.1)"
        )
    )

def index() -> rx.Component:
    return rx.vstack(
        navbar(),
        cotizador_flotante(),
        
        # --- HERO SECTION CON VIDEO ---
        rx.box(
            # Video de fondo
            rx.el.video(
                rx.el.source(
                    src="https://assets.mixkit.co/videos/preview/mixkit-printing-machine-for-t-shirts-42891-large.mp4", 
                    type="video/mp4"
                ),
                auto_play=True, loop=True, muted=True, playsinline=True,
                style={"position": "absolute", "top": "0", "left": "0", "width": "100%", "height": "100%", "objectFit": "cover", "zIndex": "0"}
            ),
            # Capa oscura para que el texto se lea
            rx.box(position="absolute", top="0", left="0", width="100%", height="100%", background="linear-gradient(to right, rgba(44,44,44,0.9) 0%, rgba(44,44,44,0.5) 100%)", z_index="1"),
            
            rx.vstack(
                rx.badge("TEXTILES Y SUBLIMACIÓN", color_scheme="orange", variant="solid", size="1"),
                rx.heading("Creamos lo que imaginas.", size=rx.breakpoints(initial="6", sm="7", md="8"), weight="bold", text_align="left", color="white", line_height="1.1"),
                rx.text("Tazas, gorras y franelas personalizadas en Caracas.", color="rgba(255,255,255,0.8)", size=rx.breakpoints(initial="2", sm="3", md="4")),
                rx.button("Ver Catálogo", on_click=rx.call_script("document.getElementById('catalogo').scrollIntoView({behavior: 'smooth'})"), size="3", bg="#D96B43", color="white", border_radius="6px", margin_top="1.5em", _hover={"bg": "#C25733"}),
                align="start", padding=rx.breakpoints(initial="4em 1em", sm="6em 2em", md="8em 4em"), width="100%", max_width="1200px", z_index="2",
            ),
            position="relative", width="100%", min_height="70vh", display="flex", align_items="center", justify_content="center", overflow="hidden"
        ),

        # CATÁLOGO
        rx.vstack(
            rx.heading("Catálogo", size="6", weight="bold", color="#2C2C2C"),
            rx.grid(
                tarjeta_producto("Taza Cerámica", 8.00, "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Acabado brillante."),
                tarjeta_producto("Gorra Premium", 12.00, "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Malla transpirable."),
                tarjeta_producto("Franela Algodón", 15.00, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Corte moderno."),
                columns=rx.breakpoints(initial="1", sm="2", md="3"),
                spacing="6", width="100%", margin_top="2em",
            ),
            padding="4em 1em", width="100%", align="center", bg="#F8FAFC", id="catalogo"
        ),

        galeria_trabajos(),

        rx.box(
            seccion_personalizador(),
            width="100%", padding="4em 1em", bg="#F8FAFC", id="personalizar"
        ),
        
        rx.vstack(
            rx.text("© 2024 SubliCaracas. Emprendimiento venezolano.", color="#94A3B8", size="1"),
            padding="2em", width="100%", bg="#0F172A", align="center"
        ),
        bg="#FFFFFF", min_height="100vh", align="center", width="100%", spacing="0",
    )

# IMPORTANTE: Asegúrate de que rxconfig.py NO tenga configurado api_url
app = rx.App(style={"font_family": "'Helvetica Neue', Helvetica, Arial, sans-serif"})
app.add_page(index)