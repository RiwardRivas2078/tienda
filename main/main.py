import reflex as rx
import urllib.parse
import base64

# --- ESTILO GLOBAL ---
font_style = {
    "font_family": "'Helvetica Neue', Helvetica, Arial, sans-serif",
}

# --- ESTADO ---
class State(rx.State):
    texto_cliente: str = ""
    logo_subido: list[str] = []
    carrito: list[dict] = []
    TASA_BCV: float = 36.50

    def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            upload_data = file.file.read()
            encoded = base64.b64encode(upload_data).decode("utf-8")
            self.logo_subido = [f"data:image/png;base64,{encoded}"]

    def limpiar_logo(self):
        self.logo_subido = []

    def agregar_al_carrito(self, nombre: str, precio: float):
        self.carrito.append({"nombre": nombre, "precio": precio})

    def quitar_del_carrito(self, index: int):
        self.carrito.pop(index)

    @rx.var
    def total_usd(self) -> float:
        return sum(item["precio"] for item in self.carrito)

    @rx.var
    def total_bs(self) -> str:
        return f"Bs. {(self.total_usd * self.TASA_BCV):,.2f}"

    @rx.var
    def link_whatsapp_cotizacion(self) -> str:
        if not self.carrito:
            return "https://wa.me/584242446795?text=Hola,%20quiero%20cotizar."
        mensaje = "Hola SubliCaracas, quiero cotizar lo siguiente:\n"
        for item in self.carrito:
            mensaje += f"- {item['nombre']} (${item['precio']})\n"
        mensaje += f"\nTotal: ${self.total_usd:.2f} / {self.total_bs}"
        return f"https://wa.me/584242446795?text={urllib.parse.quote(mensaje)}"

WHATSAPP_NUMERO = "584242446795"

# --- COMPONENTES ---

def navbar() -> rx.Component:
    return rx.box(
        rx.container(
            rx.hstack(
                rx.hstack(
                    rx.icon(tag="scissors", color="#D96B43", size=24),
                    rx.heading("SubliCaracas", size="6", weight="bold", color="#2C2C2C", letter_spacing="-0.02em"),
                    align="center",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.link("Catálogo", href="#catalogo", color="#6B7280", _hover={"color": "#D96B43"}, weight="medium"),
                    rx.link("Galería", href="#galeria", color="#6B7280", _hover={"color": "#D96B43"}, weight="medium"),
                    rx.link("Personalizar", href="#personalizar", color="#6B7280", _hover={"color": "#D96B43"}, weight="medium"),
                    rx.color_mode.button(), 
                    spacing="6", align="center",
                ),
                width="100%", align="center",
            ),
            size="4", padding_y="1.5em",
        ),
        width="100%", bg="rgba(249, 246, 240, 0.95)", backdrop_filter="blur(12px)",
        border_bottom="1px solid #E5E0D8", position="sticky", top="0", z_index="1000",
    )

def tarjeta_producto(nombre: str, precio: float, imagen: str, desc: str) -> rx.Component:
    precio_bs = f"Bs. {(precio * State.TASA_BCV):,.2f}"
    return rx.box(
        rx.vstack(
            rx.box(
                rx.image(src=imagen, width="100%", height="260px", object_fit="cover"),
                rx.badge(f"${precio:.2f}", color_scheme="orange", variant="solid", size="3", position="absolute", bottom="12px", right="12px", font_size="15px", padding="0.4em 0.8em", border_radius="full", box_shadow="sm"),
                position="relative", width="100%",
            ),
            rx.vstack(
                rx.heading(nombre, size="4", weight="bold", color="#2C2C2C"),
                rx.text(desc, size="2", color="#6B7280", min_height="40px"),
                rx.hstack(
                    rx.text(f"Bs. {precio_bs}", color="#9CA3AF", size="2", weight="medium"),
                    align="baseline", margin_bottom="1.2em"
                ),
                rx.button(
                    rx.icon(tag="plus", size=16), "Agregar", 
                    on_click=lambda: State.agregar_al_carrito(nombre, precio),
                    bg="#2C2C2C", color="#F9F6F0",
                    width="100%", border_radius="4px", size="3", 
                    _hover={"bg": "#D96B43", "transition": "0.3s"}
                ),
                align_items="start", width="100%", padding="1.2em",
            ),
            spacing="0", width="100%", bg="white",
        ),
        border="1px solid #E5E0D8", border_radius="8px", overflow="hidden", 
        _hover={"box_shadow": "0 10px 25px -5px rgba(0, 0, 0, 0.05)", "transform": "translateY(-2px)", "transition": "0.3s"},
    )

def galeria_trabajos() -> rx.Component:
    productos = [
        {"nombre": "Pijama Navideña", "precio": 18.00, "foto": "/pijama1.jpeg", "desc": "Diseño exclusivo para las fiestas."},
        {"nombre": "Pijama Ositos", "precio": 20.00, "foto": "/pijama2.jpeg", "desc": "Tela suave ideal para regalar."},
        {"nombre": "Pijama Grinch", "precio": 22.00, "foto": "/pijama3.jpeg", "desc": "Divertida y cómoda."},
        {"nombre": "Pijama Rosada", "precio": 18.00, "foto": "/pijama4.jpeg", "desc": "Para un look relajado."},
        {"nombre": "Pijama Cuadros", "precio": 20.00, "foto": "/pijama5.jpeg", "desc": "Clásico y elegante."},
    ]
    return rx.vstack(
        rx.vstack(
            rx.heading("Nuestras Creaciones", size="7", weight="bold", color="#2C2C2C"),
            rx.text("Explora nuestros diseños más recientes.", color="#6B7280", size="4"),
            align="center", margin_bottom="3em",
        ),
        rx.grid(
            *[tarjeta_producto(p["nombre"], p["precio"], p["foto"], p["desc"]) for p in productos],
            columns=rx.breakpoints(initial="1", sm="2", md="3", lg="5"),
            spacing="6", width="100%", max_width="1200px",
        ),
        padding="5em 2em", width="100%", align="center", bg="#F9F6F0", id="galeria"
    )

def seccion_personalizador() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.box(
                    rx.image(
                        src="https://images.unsplash.com/photo-1588850561407-ed78c282e89b?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
                        width="100%", max_width="350px", border_radius="8px", display="block", margin="0 auto"
                    ),
                    rx.vstack(
                        rx.cond(
                            State.logo_subido.length() > 0,
                            rx.image(
                                src=State.logo_subido[0], 
                                width="90px", 
                                mix_blend_mode="multiply", 
                                filter="drop-shadow(0px 2px 4px rgba(0,0,0,0.2)) contrast(120%)",
                                opacity="0.95"
                            )
                        ),
                        rx.cond(
                            State.texto_cliente != "",
                            rx.text(
                                State.texto_cliente, 
                                font_size="16px", font_weight="bold", color="#2C2C2C", 
                                text_align="center", text_shadow="0px 1px 2px rgba(255,255,255,0.9)",
                                margin_top="0.2em"
                            )
                        ),
                        position="absolute", top="45%", left="50%", transform="translate(-50%, -50%)", 
                        align="center", width="100%", z_index="10"
                    ),
                    position="relative", width="100%", display="flex", justify_content="center"
                ),
                rx.cond(
                    State.logo_subido.length() > 0,
                    rx.button("Quitar imagen", on_click=State.limpiar_logo, size="1", variant="soft", color_scheme="red", margin_top="1em", width="100%")
                ),
                width="50%",
            ),
            
            rx.vstack(
                rx.badge("DISEÑO PERSONALIZADO", color_scheme="orange", variant="soft", size="2", margin_bottom="0.5em"),
                rx.heading("Crea tu gorra", size="6", weight="bold", color="#2C2C2C"),
                rx.text("Sube tu diseño, escribe tu texto y visualiza el resultado.", color="#6B7280", size="3"),
                rx.divider(margin_y="1.5em", border_color="#E5E0D8"),
                
                rx.text("1. Sube tu imagen", weight="bold", size="2", color="#2C2C2C"),
                rx.upload(
                    rx.vstack(
                        rx.icon(tag="image", size=32, color="#D96B43"),
                        rx.text("Haz clic o arrastra tu diseño", size="2", color="#6B7280"),
                        rx.text("(PNG transparente)", size="1", color="#9CA3AF"),
                        align="center",
                    ),
                    id="logo_upload", border="2px dashed #D6D3D1", padding="2em", border_radius="8px", background="#FFFFFF",
                    cursor="pointer", _hover={"border_color": "#D96B43", "background": "#FFF7ED"},
                    on_drop=State.handle_upload(rx.upload_files(upload_id="logo_upload")),
                ),
                
                rx.text("2. Escribe tu texto", weight="bold", size="2", color="#2C2C2C", margin_top="1.5em"),
                rx.input(
                    placeholder="Ej: Feliz Cumpleaños...", 
                    value=State.texto_cliente, on_change=State.set_texto_cliente,
                    width="100%", size="3", border_radius="4px", border="1px solid #D6D3D1", background="white", margin_bottom="1.5em"
                ),
                
                rx.button(
                    rx.icon(tag="plus", size=16), "Agregar a cotización", 
                    on_click=lambda: State.agregar_al_carrito("Gorra Personalizada", 12.00),
                    bg="#2C2C2C", color="#F9F6F0",
                    width="100%", border_radius="4px", size="3", margin_bottom="1em",
                    _hover={"bg": "#D96B43"}
                ),
                
                rx.link(
                    rx.button("Enviar diseño por WhatsApp", bg="#25D366", color="white", width="100%", size="3", border_radius="4px", _hover={"bg": "#128C7E"}),
                    href="https://wa.me/584242446795?text=Hola,%20quiero%20una%20gorra%20personalizada", is_external=True, width="100%", text_decoration="none"
                ),
                width="50%", padding_left="4em", align_items="start"
            ),
            width="100%", align="center", spacing="8",
        ),
        padding="4em", background="#FFFFFF", border_radius="12px", border="1px solid #E5E0D8",
        box_shadow="0 10px 25px -5px rgba(0, 0, 0, 0.05)",
        width="100%", max_width="1000px", margin="0 auto"
    )

def cotizador_flotante() -> rx.Component:
    return rx.cond(
        State.carrito.length() > 0,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("Tu Cotización", size="5", weight="bold", color="#2C2C2C"),
                    rx.spacer(),
                    rx.text(f"${State.total_usd:.2f}", color="#D96B43", weight="bold", size="5"),
                ),
                rx.text(f"Total en Bs: {State.total_bs}", color="#6B7280", size="3", weight="medium"),
                rx.divider(margin_y="1em", border_color="#E5E0D8"),
                rx.vstack(
                    rx.foreach(
                        State.carrito,
                        lambda item, i: rx.hstack(
                            rx.text(item["nombre"], size="2", weight="medium", color="#2C2C2C"),
                            rx.spacer(),
                            rx.icon(tag="x", size=16, color="#EF4444", cursor="pointer", on_click=lambda: State.quitar_del_carrito(i)),
                            width="100%", align="center"
                        )
                    ),
                    max_height="200px", overflow_y="auto", width="100%"
                ),
                rx.link(
                    rx.button("Pedir por WhatsApp", bg="#25D366", color="white", width="100%", margin_top="1.5em", border_radius="4px"),
                    href=State.link_whatsapp_cotizacion, is_external=True, width="100%"
                ),
                padding="1.5em", width="100%"
            ),
            position="fixed", bottom="24px", right="24px", width="320px",
            background="white", border_radius="12px",
            box_shadow="0 20px 25px -5px rgba(0, 0, 0, 0.1)", border="1px solid #E5E0D8",
            z_index="9999"
        )
    )

def index() -> rx.Component:
    return rx.vstack(
        navbar(),
        cotizador_flotante(),
        
        # --- HERO SECTION ---
        rx.box(
            rx.image(
                src="https://images.unsplash.com/photo-1562157873-818bc0726f68?q=80&w=1920&auto=format&fit=crop",
                width="100%", height="100%", object_fit="cover",
                position="absolute", top="0", left="0", z_index="0"
            ),
            rx.box(
                position="absolute", top="0", left="0", width="100%", height="100%",
                background="linear-gradient(to right, rgba(44,44,44,0.9) 0%, rgba(44,44,44,0.4) 100%)",
                z_index="1"
            ),
            rx.vstack(
                rx.badge("TEXTILES Y SUBLIMACIÓN", color_scheme="orange", variant="solid", size="2", margin_bottom="1em"),
                rx.heading(
                    "Creamos lo que imaginas.", 
                    size="9", weight="bold", text_align="left", color="white", line_height="1.1", max_width="600px"
                ),
                rx.text(
                    "Tazas, gorras y franelas personalizadas con la mejor calidad de Caracas.", 
                    color="rgba(255,255,255,0.8)", size="5", text_align="left", max_width="500px", line_height="1.6"
                ),
                rx.hstack(
                    rx.button(
                        "Ver Catálogo", 
                        on_click=rx.call_script("document.getElementById('catalogo').scrollIntoView({behavior: 'smooth'})"), 
                        size="4", bg="#D96B43", color="white", border_radius="4px", weight="bold", _hover={"bg": "#C25733"}
                    ),
                    rx.button(
                        "Personalizar", 
                        on_click=rx.call_script("document.getElementById('personalizar').scrollIntoView({behavior: 'smooth'})"), 
                        size="4", variant="outline", color="white", border_color="white", border_radius="4px", _hover={"bg": "rgba(255,255,255,0.1)"}
                    ),
                    spacing="4", margin_top="2em"
                ),
                align="start", padding="10em 5em", width="100%", max_width="1200px", z_index="2",
            ),
            position="relative", width="100%", min_height="80vh", display="flex", align_items="center", justify_content="center", overflow="hidden"
        ),
        
        # --- CATÁLOGO ---
        rx.vstack(
            rx.heading("Catálogo", size="7", weight="bold", color="#2C2C2C", margin_bottom="2em"),
            rx.grid(
                tarjeta_producto("Taza Cerámica", 8.00, "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Acabado brillante de 11oz."),
                tarjeta_producto("Gorra Premium", 12.00, "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Malla transpirable, logo al frente."),
                tarjeta_producto("Franela Algodón", 15.00, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80", "Corte moderno, colores duraderos."),
                columns=rx.breakpoints(initial="1", sm="2", md="3"),
                spacing="8", width="100%", max_width="1200px",
            ),
            padding="5em 2em", width="100%", align="center", bg="#FFFFFF", id="catalogo"
        ),

        galeria_trabajos(),

        rx.box(
            seccion_personalizador(),
            width="100%", padding="5em 2em", bg="#F9F6F0", id="personalizar"
        ),
        
        rx.vstack(
            rx.text("© 2024 SubliCaracas. Emprendimiento venezolano.", color="#9CA3AF", size="2"),
            padding="3em", width="100%", bg="#2C2C2C", border_top="1px solid #E5E0D8",
            align="center"
        ),
        bg="#F9F6F0", min_height="100vh", align="center", width="100%", spacing="0",
    )

app = rx.App(style=font_style)
app.add_page(index)