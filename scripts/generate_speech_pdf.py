from pathlib import Path

from fpdf import FPDF

OUTPUT = Path(__file__).resolve().parents[1] / "Speach de llamadas.pdf"

ARIAL = "C:/Windows/Fonts/arial.ttf"
ARIAL_BD = "C:/Windows/Fonts/arialbd.ttf"
ARIAL_IT = "C:/Windows/Fonts/ariali.ttf"
ARIAL_BI = "C:/Windows/Fonts/arialbi.ttf"

PRIMARY = (33, 64, 105)
ACCENT_BG = (232, 238, 248)
MUTED = (110, 110, 110)


class SpeechPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Arial", "I", 9)
        self.set_text_color(*MUTED)
        self.cell(0, 8, "Speech de llamadas — Causal A.I. Digital", align="R")
        self.ln(10)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)


def build():
    pdf = SpeechPDF(format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_font("Arial", "", ARIAL)
    pdf.add_font("Arial", "B", ARIAL_BD)
    pdf.add_font("Arial", "I", ARIAL_IT)
    pdf.add_font("Arial", "BI", ARIAL_BI)
    pdf.add_page()

    title(pdf, "Speech Completo — Causal A.I. Digital")
    subtitle(pdf, "Guion de llamadas en frío para empresas importadoras")
    pdf.ln(4)

    section(pdf, "1. Apertura — Filtrado al dueño")
    line(pdf, "“Buenos días, ¿podría comunicarme con el dueño o el encargado comercial, por favor?”")
    stage(pdf, "(Cuando lo pasan al encargado:)")
    line(
        pdf,
        "“Buenos días, señor [apellido]. Le habla Jesús Nicho, de la empresa Causal A.I. Digital. "
        "Le comentaré brevemente el motivo de mi llamada: trabajamos desarrollando páginas web para "
        "empresas importadoras del Perú, y al revisar el sector vimos que [nombre de la empresa] "
        "aparece en Google Maps con su dirección, pero no tiene una página web propia que muestre "
        "su catálogo cuando alguien busca los productos que ustedes importan. Por eso quise "
        "contactarlo personalmente. ¿Me regala dos minutos?”",
    )

    section(pdf, "2. Cuerpo — Propuesta de valor")
    stage(pdf, "(Si dice que sí:)")
    line(
        pdf,
        "“Le agradezco. El punto es simple: hoy la mayoría de personas busca en Google antes de "
        "comprar. Aparecer en Google Maps sirve para que lo ubiquen si ya saben quién es usted o "
        "pasan cerca de su local — pero cuando un cliente nuevo busca un producto en Google, Maps "
        "no le muestra su catálogo, no le muestra precios, no le permite cotizar. Esos clientes "
        "terminan llegando a la competencia que sí tiene web, muchas veces sin que el dueño se "
        "entere. Lo que nosotros hacemos es resolver exactamente eso — una página web profesional "
        "que complementa su ficha de Maps, muestra su catálogo, transmite confianza y captura las "
        "ventas que hoy se están perdiendo.”",
    )

    section(pdf, "3. Pregunta de descubrimiento")
    line(
        pdf,
        "“Antes de continuar, una pregunta para enfocar la conversación: ¿cómo llegan hoy a ustedes "
        "los clientes nuevos — más por recomendación, redes sociales, o vienen directo a la tienda?”",
    )
    stage(
        pdf,
        "(Escuchá la respuesta. Esto te dice dónde duele. Adaptá tu cierre según lo que diga.)",
    )

    section(pdf, "4. Manejo de objeciones — Las 5 más comunes")
    objection(
        pdf,
        "“¿Cómo sacaron mi número?”",
        "“Es una pregunta justa, señor [apellido], se la respondo de frente. Su empresa aparece en "
        "directorios públicos de importadoras del Perú — está su razón social, RUC y número de "
        "contacto comercial. Yo lo que hago es revisar empresas del rubro que no tienen presencia "
        "web y los contacto directamente. Y mire, justamente por eso lo llamo: si su número está en "
        "directorios públicos y su empresa aparece en Google Maps con su dirección, pero no tiene "
        "una web propia que muestre su catálogo cuando alguien busca sus productos en Google, ese "
        "es exactamente el problema que nosotros resolvemos.”",
    )
    objection(
        pdf,
        "“No me interesa / ya tenemos quien nos lleva eso”",
        "“Lo entiendo perfectamente. Solo una pregunta antes de cortar, si me lo permite: ¿la web "
        "actual les está trayendo cotizaciones nuevas todos los meses? Si la respuesta es sí, le "
        "agradezco su tiempo. Si es no, justo de eso quería hablarle.”",
    )
    objection(
        pdf,
        "“Mándame la información por correo”",
        "“Con gusto se la envío, pero le soy honesto: si le mando un correo genérico va a terminar "
        "mezclado con todos los demás. Prefiero algo distinto: déjeme preparar una página web ya "
        "armada para su empresa y se la envío para que la vea con sus propios ojos. Es más concreto "
        "que cualquier propuesta en PDF.”",
    )
    objection(
        pdf,
        "“¿Cuánto cuesta?”",
        "“Buena pregunta, y le respondo con honestidad: depende de lo que necesiten. No es lo mismo "
        "una web de presencia institucional que una con catálogo de 200 productos. Pero le propongo "
        "algo mejor: déjeme prepararle la página terminada primero, sin cobrarle nada, y cuando la "
        "vea conversamos del precio sabiendo exactamente qué está comprando.”",
    )
    objection(
        pdf,
        "“Yo vendo bien por Facebook / WhatsApp, no necesito web”",
        "“Lo entiendo, y le creo. Pero le hago una pregunta honesta: si mañana Facebook le cambia el "
        "algoritmo o le bloquea la cuenta — pasa todos los días — ¿cuánto de su negocio se va con "
        "esa cuenta? La página web es el único activo digital que es 100% suyo. Lo demás es "
        "alquilado.”",
    )

    section(pdf, "5. Cierre — Propuesta de demo concreta")
    line(
        pdf,
        "“Le propongo algo distinto a lo que normalmente le ofrecen, señor [apellido]. En lugar de "
        "hacerle perder tiempo con reuniones largas y propuestas teóricas, voy a preparar una "
        "**página web ya terminada para [nombre de la empresa]** — con su catálogo, sus productos y "
        "su información de contacto — y se la envío para que la vea con sus propios ojos.”",
    )
    line(
        pdf,
        "“Si le gusta tal cual está, perfecto. Si quiere modificar colores, agregar o quitar "
        "productos, cambiar textos, ajustar secciones — me lo dice y lo modificamos las veces que "
        "sea necesario hasta que quede exactamente como usted la quiere. Recién ahí conversamos del "
        "cierre, sin presión.”",
    )
    line(
        pdf,
        "“Y para que tenga toda la flexibilidad cuando llegue ese momento: trabajamos con **todas "
        "las modalidades de pago** — transferencia bancaria, Yape, Plin, depósito en cuenta, tarjeta "
        "de crédito o débito, e incluso factura a 30 días si así manejan ustedes con sus "
        "proveedores. Lo que más le acomode.”",
    )

    section(pdf, "6. Confirmación de envío")
    line(
        pdf,
        "“Para enviarle la página de muestra: ¿a este mismo número de WhatsApp se la hago llegar, o "
        "prefiere que la mande a otro contacto? En **5 a 7 días hábiles** le estaría enviando el "
        "enlace para que la revise con calma desde su celular o computadora. Le agradezco mucho la "
        "confianza, señor [apellido]. Cualquier consulta antes de eso, no dude en escribirme "
        "directamente. Que tenga buen día.”",
    )

    section(pdf, "7. Preguntas frecuentes — Respuestas preparadas")
    faq(
        pdf,
        "“Pero yo ya aparezco en Google Maps con mi dirección, ¿para qué necesito una web?”",
        "“Buena pregunta y se la respondo directo: Google Maps es una ficha de su local — sirve "
        "para que lo encuentren físicamente si ya saben quién es usted o pasan por la zona. Pero "
        "cuando un cliente nuevo busca en Google algo como ‘importadora de [tal producto] en Lima’, "
        "Maps no le va a mostrar su catálogo, no le va a mostrar sus precios, ni le va a permitir "
        "cotizar. Una web hace lo que Maps no hace: muestra exactamente qué vende, transmite "
        "confianza, y captura al cliente que está investigando antes de comprar. Y lo mejor es que "
        "**ambas se complementan** — su web puede salir junto con su ficha de Maps en los "
        "resultados de Google, reforzando ambas presencias en lugar de competir.”",
    )
    faq(
        pdf,
        "“¿Y por qué me la mandarías terminada sin cobrarme nada antes?”",
        "“Justamente porque sé que el problema en este rubro no es el precio, es la confianza. Mil "
        "personas pueden prometerle una página linda — pocas la entregan. Yo prefiero invertir mi "
        "tiempo y mostrarle algo real, funcionando, antes que convencerlo con palabras. Si le gusta, "
        "conversamos. Si no, no perdió nada y al menos se queda con la idea clara de cómo se podría "
        "ver su empresa en internet.”",
    )
    faq(
        pdf,
        "“¿En cuánto tiempo me la entregan?”",
        "“Entre 5 y 7 días hábiles tiene la primera versión lista para revisar. La diferencia con "
        "otras agencias es que no le pedimos que apruebe un boceto en papel — directamente se la "
        "entregamos funcionando, con su catálogo cargado y lista para que cualquier persona la vea "
        "desde Google.”",
    )
    faq(
        pdf,
        "“¿Qué información van a necesitar de mi empresa?”",
        "“Lo mínimo indispensable: razón social, RUC para que después pueda emitir factura "
        "electrónica si lo desea, datos de contacto, y el catálogo de productos principales — "
        "nombres y, si tiene, fotos. Si no tiene fotos profesionales, le damos opciones. El resto — "
        "textos, diseño, estructura — lo armamos nosotros y usted solo aprueba.”",
    )
    faq(
        pdf,
        "“¿Y después yo voy a poder modificar la página, o dependo siempre de ustedes?”",
        "“Las dos opciones están sobre la mesa. Si quiere manejarla usted, se la entregamos con un "
        "panel sencillo donde agrega productos, cambia precios y sube fotos sin tocar código. Si "
        "prefiere que nosotros nos encarguemos, tenemos un plan de mantenimiento mensual. Usted "
        "decide cómo se siente más cómodo.”",
    )
    faq(
        pdf,
        "“¿Qué incluye exactamente? ¿Dominio, correo corporativo, todo eso?”",
        "“Incluye dominio propio (algo como suempresa.com.pe), el hosting donde se aloja la página, "
        "correos corporativos profesionales — del tipo gerencia@suempresa.com.pe en lugar del "
        "Hotmail o Gmail —, integración con WhatsApp Business para que los clientes le escriban "
        "directo, y el posicionamiento básico en Google para que aparezca cuando busquen sus "
        "productos.”",
    )
    faq(
        pdf,
        "“¿Cuánto cuesta? Necesito al menos un rango.”",
        "“Le soy honesto: depende del tamaño del catálogo y las funciones que necesite, por eso es "
        "difícil tirarle un número exacto sin verlo. Pero el modelo ya se lo expliqué: usted **no "
        "paga un sol hasta que vea la página terminada y me diga ‘esto sí lo quiero’**. El precio se "
        "conversa cuando ya sabe exactamente qué está comprando — no antes.”",
    )
    faq(
        pdf,
        "“¿Tienen otros clientes del rubro? ¿Puedo ver ejemplos?”",
        "“Sí. Junto con la página de muestra le voy a enviar enlaces a webs de otras empresas "
        "importadoras que hemos desarrollado para que las revise. Y si quiere referencias directas "
        "— el contacto de algún cliente actual para que le pregunte cómo fue el proceso — se las "
        "paso sin problema. La transparencia es parte del servicio.”",
    )
    faq(
        pdf,
        "“¿Cómo sé que no es una estafa? Hay mucha gente vendiendo humo en este rubro.”",
        "“Es una preocupación totalmente válida y la respeto. Justamente por eso le envío la web "
        "terminada **antes** de cobrarle. Una estafa le pide pago por adelantado y desaparece. "
        "Nosotros le entregamos primero, usted ve el trabajo, lo prueba, y recién ahí decide si "
        "seguimos. En este modelo el riesgo lo asumimos nosotros — no usted.”",
    )
    faq(
        pdf,
        "“¿Y si la página no me gusta o no me convence?”",
        "“No pasa absolutamente nada. Usted me dice ‘mira, no es lo que necesitaba’ y ahí termina la "
        "conversación. No firma nada por adelantado, no paga nada. Es un trabajo a riesgo nuestro "
        "porque confiamos en lo que hacemos — y porque sabemos que la mayoría sí queda conforme "
        "cuando ve el resultado.”",
    )
    faq(
        pdf,
        "“Yo ya tengo un dominio comprado y una página vieja. ¿Sirve?”",
        "“Sí, perfecto. Si ya tiene dominio lo respetamos — incluso conviene mantenerlo porque no "
        "pierde el posicionamiento que ya haya ganado en Google. Y si la página vieja tiene "
        "contenido rescatable — fotos, descripciones, datos —, lo migramos. Lo que no sirva, lo "
        "reemplazamos por algo mejor.”",
    )
    faq(
        pdf,
        "“¿Y para los pagos? ¿Cuándo y cómo se cobra?”",
        "“Solo cuando usted aprueba la versión final. Y como le mencioné, manejamos todas las "
        "modalidades: transferencia, Yape, Plin, depósito, tarjeta, e incluso factura a 30 días si "
        "lo necesita. Lo importante es que el cobro nunca va antes de que usted vea y apruebe el "
        "trabajo.”",
    )

    pdf.output(str(OUTPUT))
    print(f"PDF generado en: {OUTPUT}")


RESET = {"new_x": "LMARGIN", "new_y": "NEXT"}


def title(pdf: FPDF, text: str) -> None:
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(*PRIMARY)
    pdf.multi_cell(0, 9, text, align="C", **RESET)
    pdf.set_text_color(0, 0, 0)


def subtitle(pdf: FPDF, text: str) -> None:
    pdf.set_font("Arial", "I", 11)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 6, text, align="C", **RESET)
    pdf.set_text_color(0, 0, 0)


def section(pdf: FPDF, text: str) -> None:
    pdf.ln(5)
    pdf.set_font("Arial", "B", 13)
    pdf.set_fill_color(*ACCENT_BG)
    pdf.set_text_color(*PRIMARY)
    pdf.cell(0, 9, text, fill=True, **RESET)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def line(pdf: FPDF, text: str) -> None:
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, text, markdown=True, **RESET)
    pdf.ln(2)


def stage(pdf: FPDF, text: str) -> None:
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 6, text, **RESET)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def objection(pdf: FPDF, question: str, answer: str) -> None:
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(*PRIMARY)
    pdf.multi_cell(0, 6, "•  " + question, **RESET)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, answer, **RESET)
    pdf.ln(3)


def faq(pdf: FPDF, question: str, answer: str) -> None:
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(*PRIMARY)
    pdf.multi_cell(0, 6, "•  " + question, **RESET)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, answer, markdown=True, **RESET)
    pdf.ln(3)


if __name__ == "__main__":
    build()
