import reflex as rx
import urllib.parse
import base64
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from functools import lru_cache
import urllib3

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
    
    # Carrito: Ahora incluye la talla
    # {"nombre": str, "precio": float, "cantidad": int, "talla": str}
    carrito: list[dict] = []
    TASA_BCV: float = TASA_ACTUAL
    FECHA: str = FECHA_ACTUAL

    # Variables para el modal de tallas
    mostrar_modal: bool = False
    producto_pendiente_nombre: str = ""
    producto_pendiente_precio: float = 0.0
    talla_seleccionada: str = "M"

    def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            upload_data = file.file.read()
            encoded = base64.b64encode(upload_data).decode("utf-8")
            self.logo_subido = [f"data:image/png;base64,{encoded}"]

    def limpiar_logo(self):
        self.logo_subido = []

    # --- LÓGICA DE CARRITO Y MODAL ---
    def abrir_modal_tallas(self, nombre: str, precio: float):
        self.producto_pendiente_nombre = nombre
        self.producto_pendiente_precio = precio
        self.talla_seleccionada = "M" # Talla por defecto
        self.mostrar_modal = True

    def cerrar_modal(self):
        self.mostrar_modal = False

    def confirmar_agregar(self):
        self.agregar_al_carrito(self.producto_pendiente_nombre, self.producto_pendiente_precio, self.talla_seleccionada)
        self.mostrar_modal = False

    def agregar_al_carrito(self, nombre: str, precio: float, talla: str = "Única"):
        # Verificamos si el producto exacto (con la misma talla) ya está en el carrito
        for item in self.carrito:
            if item["nombre"] == nombre and item["talla"] == talla:
                item["cantidad"] += 1
                return
        self.carrito.append({"nombre": nombre, "precio": precio, "cantidad": 1, "talla": talla})

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
        mensaje = "Hola SubliCaracas, quiero confirmar mi pedido:\n\n"
        for item in self.carrito:
            subtotal = item['precio'] * item['cantidad']
            # Formato: - Pijama Navideña (Talla: M) x2 ($40.00)
            mensaje += f"- {item['nombre']} (Talla: {item['talla']}) x{item['cantidad']} (${subtotal:.2f})\n"
        mensaje += f"\nTotal: ${self.total_usd:.2f} / {self.total_bs}"
        return f"https://wa.me/584242446795?text={urllib.parse.quote(mensaje)}"

WHATSAPP_NUMERO = "584242446795"

# --- PALETA DE COLORES ---
BG_WHITE = "#FFFFFF"
BG_SOFT = "#FAFAF9"      
TEXT_DARK = "#1C1917"    
TEXT_GRAY = "#78716C"
ACCENT = "#D96B43"       

# --- COMPONENTES ---

def ticker_tasa() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(f"Tasa Oficial BCV: {State.TASA_BCV:.2f} Bs/$", size="1", color="white", weight="bold"),
            rx.text(f"| Actualizado: {State.FECHA}", size="1", color="rgba(255,255,255,0.8)"),
            spacing="2", justify="center", width="100%"
        ),
        bg=TEXT_DARK, padding="0.6em", width="100%"
    )

def navbar() -> rx.Component:
    return rx.vstack(
        ticker_tasa(),
        rx.box(
            rx.container(
                rx.flex(
                    rx.hstack(
                        rx.icon(tag="scissors", color=ACCENT, size=24),
                        rx.heading("SubliCaracas", size="5", weight="bold", color=TEXT_DARK, letter_spacing="-0.02em"),
                        align="center",
                    ),
                    rx.flex(
                        rx.link("Catálogo", href="#catalogo", color=TEXT_GRAY, weight="medium", _hover={"color": TEXT_DARK}),
                        rx.link("Galería", href="#galeria", color=TEXT_GRAY, weight="medium", _hover={"color": TEXT_DARK}),
                        rx.link("Cotizar Diseño", href="#personalizar", color=TEXT_GRAY, weight="medium", _hover={"color": TEXT_DARK}),
                        spacing="6", direction=rx.breakpoints(initial="row", sm="row"), justify="center",
                    ),
                    direction=rx.breakpoints(initial="column", md="row"),
                    justify="between", align="center", width="100%", gap="1em", padding_y="1.2em"
                ),
                size="4"
            ),
            width="100%", bg="rgba(255, 255, 255, 0.95)", backdrop_filter="blur(12px)", border_bottom="1px solid #E7E5E4", position="sticky", top="0", z_index="1000",
        ),
        spacing="0", width="100%"
    )

# --- MODAL DE SELECCIÓN DE TALLAS ---
def modal_tallas() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(
                    rx.heading("Selecciona tu talla", size="5", weight="bold", color=TEXT_DARK),
                ),
                rx.text(f"Producto: {State.producto_pendiente_nombre}", color=TEXT_GRAY, size="2", margin_bottom="1em"),
                
                # Botones de tallas
                rx.hstack(
                    *[rx.button(
                        talla, 
                        on_click=lambda t=talla: State.set_talla_seleccionada(t),
                        variant=rx.cond(State.talla_seleccionada == talla, "solid", "outline"),
                        color_scheme=rx.cond(State.talla_seleccionada == talla, "orange", "gray"),
                        border_radius="8px", width="60px", size="3"
                    ) for talla in ["S", "M", "L", "XL"]],
                    spacing="3", justify="center", width="100%", margin_y="1.5em"
                ),
                
                rx.flex(
                    rx.dialog.close(
                        rx.button("Cancelar", variant="soft", color_scheme="gray", width="100%", border_radius="8px", on_click=State.cerrar_modal),
                    ),
                    rx.button("Agregar al Carrito", bg=ACCENT, color="white", width="100%", border_radius="8px", on_click=State.confirmar_agregar),
                    spacing="3", width="100%", margin_top="1em"
                ),
                width="100%"
            ),
            max_width="400px", padding="2em"
        ),
        open=State.mostrar_modal,
        on_open_change=State.set_mostrar_modal
    )

# --- TARJETA DE PRODUCTO (Modificada para saber si tiene tallas) ---
def tarjeta_producto(nombre: str, precio: float, imagen: str, desc: str, tiene_tallas: bool = False) -> rx.Component:
    precio_bs = f"Bs. {(precio * State.TASA_BCV):,.2f}"
    
    # Lógica del botón: Si tiene tallas abre el modal, sino agrega directo.
    accion_boton = rx.cond(
        tiene_tallas,
        lambda: State.abrir_modal_tallas(nombre, precio),
        lambda: State.agregar_al_carrito(nombre, precio, "Única")
    )

    return rx.box(
        rx.vstack(
            rx.box(
                rx.image(src=imagen, width="100%", height="240px", object_fit="cover", object_position="center"),
                rx.badge(f"${precio:.2f}", color_scheme="orange", variant="solid", size="1", position="absolute", top="12px", right="12px", border_radius="full"),
                position="relative", width="100%",
            ),
            rx.vstack(
                rx.heading(nombre, size="3", weight="bold", color=TEXT_DARK),
                rx.text(desc, size="1", color=TEXT_GRAY, min_height="30px"),
                rx.hstack(
                    rx.text(f"Bs. {precio_bs}", color=TEXT_GRAY, size="1"),
                    rx.spacer(),
                    rx.button(
                        rx.icon(tag="plus", size=14), "Agregar", 
                        on_click=accion_boton,
                        bg="#F5F5F4", color=TEXT_DARK, border_radius="8px", size="1", 
                        _hover={"bg": ACCENT, "color": "white"}
                    ),
                ),
                align_items="start", width="100%", padding="1.2em",
            ),
            spacing="0", width="100%", bg="white",
        ),
        border="1px solid #E7E5E4", border_radius="12px", overflow="hidden", width="100%",
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
        rx.heading("Colección de Pijamas", size="6", weight="bold", color=TEXT_DARK, letter_spacing="-0.02em"),
        rx.grid(
            # Aquí activamos 'tiene_tallas=True' para las pijamas
            *[tarjeta_producto(p["nombre"], p["precio"], p["foto"], p["desc"], tiene_tallas=True) for p in productos],
            columns=rx.breakpoints(initial="2", sm="2", md="3", lg="5"),
            spacing="4", width="100%", margin_top="2em",
        ),
        padding="4em 2em", width="100%", align="center", bg=BG_SOFT, id="galeria"
    )

def seccion_personalizador() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.vstack(
                rx.heading("Cotiza tu diseño personalizado", size="6", weight="bold", color=TEXT_DARK, letter_spacing="-0.02em"),
                rx.text("Sube tu logo y cuéntanos qué necesitas. Te enviaremos una muestra por WhatsApp.", color=TEXT_GRAY, size="3", line_height="1.6"),
                rx.divider(margin_y="1.5em", border_color="#E7E5E4"),
                rx.text("Garantía SubliCaracas: Si no te gusta el diseño, no pagas nada.", color=ACCENT, weight="bold", size="2"),
                align="start",
                width=rx.breakpoints(initial="100%", md="50%"),
                padding_right=rx.breakpoints(initial="0", md="2em"),
                margin_bottom=rx.breakpoints(initial="2em", md="0"),
            ),
            rx.vstack(
                rx.text("1. Sube tu logo (PNG)", weight="bold", size="2", color=TEXT_DARK),
                rx.upload(
                    rx.vstack(
                        rx.icon(tag="cloud_upload", size=32, color=ACCENT),
                        rx.text("Haz clic o arrastra tu archivo", size="2", color=TEXT_GRAY), 
                        align="center"
                    ),
                    id="logo_upload", border="2px dashed #D6D3D1", padding="2.5em", border_radius="12px", background="#FFFFFF",
                    on_drop=State.handle_upload(rx.upload_files(upload_id="logo_upload")), width="100%",
                    _hover={"border_color": ACCENT, "background": "#FFF7ED"}
                ),
                rx.cond(
                    State.logo_subido.length() > 0,
                    rx.button("Quitar imagen", on_click=State.limpiar_logo, size="1", variant="soft", color_scheme="red", margin_top="0.5em", width="100%")
                ),
                rx.text("2. Describe tu idea", weight="bold", size="2", color=TEXT_DARK, margin_top="1.5em"),
                rx.input(placeholder="Ej: Gorra con el logo de mi empresa...", value=State.texto_cliente, on_change=State.set_texto_cliente, width="100%", size="3", margin_bottom="1.5em", border_radius="8px", bg="#FFFFFF", border="1px solid #D6D3D1", color=TEXT_DARK),
                
                rx.link(
                    rx.button(
                        rx.image(src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg", width="20px", margin_right="8px"),
                        "Solicitar Cotización por WhatsApp", 
                        bg="#25D366", color="white", width="100%", size="3", border_radius="8px", weight="bold",
                        _hover={"bg": "#1EA952"}
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
        background="#FFFFFF", border="1px solid #E7E5E4", border_radius="16px", width="100%", max_width="1000px", margin="0 auto",
        box_shadow="0 4px 6px -1px rgba(0,0,0,0.05)"
    )

def footer() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="instagram", size=24, color=TEXT_GRAY, cursor="pointer", _hover={"color": ACCENT}),
                rx.icon(tag="music", size=24, color=TEXT_GRAY, cursor="pointer", _hover={"color": ACCENT}),
                spacing="6", margin_bottom="1em"
            ),
            rx.text("© 2024 SubliCaracas. Diseño y calidad sin compromisos.", color=TEXT_GRAY, size="1"),
            align="center", padding="3em", width="100%", bg="#FFFFFF", border_top="1px solid #E7E5E4"
        ),
        width="100%"
    )

# --- CARRITO FLOTANTE (Modificado para mostrar tallas) ---
def cotizador_flotante() -> rx.Component:
    return rx.cond(
        State.carrito.length() > 0,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("Tu Pedido", size="4", weight="bold", color=TEXT_DARK),
                    rx.spacer(),
                    rx.text(f"${State.total_usd:.2f}", color=ACCENT, weight="bold", size="4")
                ),
                rx.text(f"Total en Bs: {State.total_bs}", color=TEXT_GRAY, size="2"),
                rx.divider(margin_y="0.5em", border_color="#E7E5E4"),
                rx.vstack(
                    rx.foreach(
                        State.carrito, 
                        lambda item, i: rx.hstack(
                            # Mostramos la talla en el carrito
                            rx.text(f"{item['nombre']} (Talla: {item['talla']}) x{item['cantidad']}", size="2", weight="medium", color=TEXT_DARK),
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
                rx.link(rx.button("Confirmar Pedido por WhatsApp", bg="#25D366", color="white", width="100%", margin_top="0.5em", size="3", border_radius="8px"), href=State.link_whatsapp_cotizacion, is_external=True, width="100%"),
                padding="1.5em", width="100%"
            ),
            position="fixed", bottom="100px", right="20px", width="calc(100% - 40px)", max_width="340px", background="white", border_radius="12px", border="1px solid #E2E8F0", z_index="9998", box_shadow="0 10px 25px -5px rgba(0,0,0,0.1)"
        )
    )

# --- BOTÓN FLOTANTE DE WHATSAPP ---
def boton_flotante_whatsapp() -> rx.Component:
    return rx.link(
        rx.image(
            src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg",
            width="65px",
            height="65px",
            position="fixed",
            bottom="20px",
            right="20px",
            z_index="9999",
            cursor="pointer",
            _hover={"transform": "scale(1.1)", "transition": "all 0.3s ease"},
            filter="drop-shadow(0px 8px 16px rgba(0,0,0,0.3))"
        ),
        href="https://wa.me/584242446795?text=Hola,%20quiero%20más%20información",
        is_external=True
    )

def index() -> rx.Component:
    return rx.vstack(
        modal_tallas(), # <-- Agregamos el modal aquí
        navbar(),
        boton_flotante_whatsapp(),
        cotizador_flotante(),
        
        # HERO SECTION
        rx.box(
            rx.image(
                src="https://images.unsplash.com/photo-1523381210434-271e8be1f52b?q=80&w=1920&auto=format&fit=crop", 
                width="100%", height="100%", object_fit="cover", position="absolute", top="0", left="0", z_index="0"
            ),
            rx.box(position="absolute", top="0", left="0", width="100%", height="100%", background="linear-gradient(to right, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.4) 100%)", z_index="1"),
            
            rx.vstack(
                rx.badge("TEXTILES Y SUBLIMACIÓN", color_scheme="orange", variant="solid", size="1"),
                rx.heading("Creamos lo que imaginas.", size=rx.breakpoints(initial="7", sm="8", md="9"), weight="bold", text_align="left", color=TEXT_DARK, line_height="1.1", letter_spacing="-0.03em"),
                rx.text("Tazas, gorras y franelas personalizadas en Caracas.", color=TEXT_GRAY, size=rx.breakpoints(initial="3", sm="4", md="4")),
                rx.button("Ver Catálogo", on_click=rx.call_script("document.getElementById('catalogo').scrollIntoView({behavior: 'smooth'})"), size="3", bg=ACCENT, color="white", border_radius="8px", margin_top="1.5em", _hover={"bg": "#C25733"}),
                align="start", padding=rx.breakpoints(initial="6em 2em", sm="8em 3em", md="10em 5em"), width="100%", max_width="1200px", z_index="2",
            ),
            position="relative", width="100%", min_height="70vh", display="flex", align_items="center", justify_content="center", overflow="hidden"
        ),
        
        # CATÁLOGO PRINCIPAL (Tazas, Gorras, etc. - Talla Única)
        rx.vstack(
            rx.heading("Catálogo Destacado", size="6", weight="bold", color=TEXT_DARK, letter_spacing="-0.02em"),
            rx.grid(
                tarjeta_producto("Taza Cerámica", 8.00, "https://images.unsplash.com/photo-1577937927133-66ef06acdf18?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Acabado brillante.", tiene_tallas=False),
                tarjeta_producto("Gorra Premium", 12.00, "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Malla transpirable.", tiene_tallas=False),
                tarjeta_producto("Franela Algodón", 15.00, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Corte moderno.", tiene_tallas=True), # Franela SÍ tiene tallas
                tarjeta_producto("Termo Deportivo", 22.00, "https://images.unsplash.com/photo-1602143407151-7111542de6e8?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Acero inoxidable.", tiene_tallas=False),
                tarjeta_producto("Llavero Personalizado", 5.00, "https://images.unsplash.com/photo-1584916201218-f4242ceb4809?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Acrílico resistente.", tiene_tallas=False),
                tarjeta_producto("Cojín Sublimado", 12.00, "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Tela suave y cómoda.", tiene_tallas=False),
                tarjeta_producto("Bolso Tote", 10.00, "https://images.unsplash.com/photo-1544816155-12df9643f363?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Ideal para el día a día.", tiene_tallas=False),
                columns=rx.breakpoints(initial="2", sm="2", md="3", lg="4"),
                spacing="6", width="100%", margin_top="2em",
            ),
            padding="4em 2em", width="100%", align="center", bg=BG_WHITE, id="catalogo"
        ),

        galeria_trabajos(),

        rx.box(
            seccion_personalizador(),
            width="100%", padding="4em 2em", bg=BG_SOFT, id="personalizar"
        ),
        
        footer(),
        
        bg=BG_WHITE, min_height="100vh", align="center", width="100%", spacing="0",
    )

app = rx.App(style={"font_family": "'Inter', system-ui, sans-serif"})
app.add_page(index)