from fpdf import FPDF

# Crear PDF
pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# Título
pdf.set_font("Arial", 'B', 16)
pdf.cell(0, 10, "Análisis del Grupo de WhatsApp: Viaje de Egresados Bariloche 2027", ln=True, align='C')

# Secciones
pdf.set_font("Arial", 'B', 12)
pdf.ln(10)
pdf.cell(0, 10, "Resumen General:", ln=True)

pdf.set_font("Arial", '', 11)
general_summary = """
El grupo se conformó para coordinar el viaje de egresados a Bariloche 2027.
Predomina un clima de colaboración, aunque hay diferencias de opinión sobre la empresa a contratar.
Travel Rock parte con ventaja por haber iniciado el contacto, presentar su propuesta primero y tener experiencias positivas de varios padres.
"""
pdf.multi_cell(0, 8, general_summary)

# Perfiles
pdf.set_font("Arial", 'B', 12)
pdf.ln(5)
pdf.cell(0, 10, "Perfiles Psicológicos Destacados:", ln=True)

pdf.set_font("Arial", '', 11)
profiles = [
    ("Fede", "Organizador, pragmático, conciliador."),
    ("Selva (Mama Gael)", "Motivadora, proactiva, comprometida con la inclusión."),
    ("Nati (Mama Joaquín)", "Ejecutora, firme, orientada a resultados y negociación."),
    ("Gian (Papa Mia)", "Analítico, con experiencia, defensor de Travel Rock."),
    ("Mechi (Mama Trini)", "Comunicadora, decidida por Travel Rock, abierta al diálogo."),
    ("Susana (Mama Mia)", "Práctica, con experiencia previa, apoyo constante."),
    ("Vane", "Crítica, preocupada por la seguridad y reputación de la empresa."),
    ("Josnay", "Empática, abierta a decisiones grupales, condicionada por nacionalidad.")
]

for name, desc in profiles:
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, f"- {name}:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 8, f"  {desc}")

# Tendencia
pdf.set_font("Arial", 'B', 12)
pdf.ln(5)
pdf.cell(0, 10, "Tendencia de Elección de Empresa:", ln=True)
pdf.set_font("Arial", '', 11)
trend = """
Travel Rock lidera la preferencia por:
- Ser la primera en presentarse y contactar al grupo.
- Experiencias positivas de padres anteriores.
- Ofrecer múltiples beneficios: shows, vuelos charter, seguridad, promociones familiares.
Maxdream, Baxter y Flecha son evaluadas, pero no logran el mismo respaldo.
"""
pdf.multi_cell(0, 8, trend)

# Conclusión
pdf.set_font("Arial", 'B', 12)
pdf.ln(5)
pdf.cell(0, 10, "Conclusión:", ln=True)
pdf.set_font("Arial", '', 11)
conclusion = """
Travel Rock tiene el mayor respaldo y probablemente será la empresa elegida, salvo que otra empresa presente una propuesta muy superior o ocurra un hecho negativo que cambie la percepción del grupo.
"""
pdf.multi_cell(0, 8, conclusion)

# Guardar PDF
pdf_path = "/mnt/data/analisis_viaje_egresados_bariloche2027.pdf"
pdf.output(pdf_path)

pdf_path
