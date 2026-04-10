import os
import io
import base64
import random
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF para manejar el PDF

app = Flask(__name__)

# --- CONFIGURACIÓN DE RUTAS ---
FOLDER_FUENTES = "fuentes"
FOLDER_IMAGENES = "imagenes"
# Definimos los posibles fondos
FONDO_TIVE1 = os.path.join("static", "tive.png")
FONDO_TIVE2 = os.path.join("static", "tive2.png")
FONDO_TIVE3 = os.path.join("static", "tive3.png")

# Definición de fuentes
FUENTE_GENERAL = os.path.join(FOLDER_FUENTES, "phagspa.ttf")
FUENTE_ARIAL = os.path.join(FOLDER_FUENTES, "arial.ttf")
FUENTE_ARIALBD = os.path.join(FOLDER_FUENTES, "arialbd.ttf")
FUENTE_ROBOTOBD = os.path.join(FOLDER_FUENTES, "robotobd.ttf")

COLOR_GRIS_73 = (130, 130, 130)  
COLOR_NEGRO = (0, 0, 0)
COLOR_GRISCLARO = (203, 203, 203)
COORD_FOTO = (1159, 2245) 
# Coordenada (X, Y) en tive.png donde se pegará el recorte del PDF
COORD_PEGADO_PDF = (231, 196)

CONFIG_CAMPOS = {
    "verificacion": (845, 288, 30, None, COLOR_NEGRO), 
    "n_titulo": (670, 331, 30, None, COLOR_NEGRO),
    "fecha": (638, 374, 30, None, COLOR_NEGRO),
    "zona_registral": (187, 689, 34, FUENTE_ARIALBD, COLOR_GRIS_73),
    "sede": (185, 735, 34, FUENTE_ARIALBD, COLOR_GRIS_73),
    "partida": (501, 840, 30, None, COLOR_NEGRO), 
    "dua": (375, 903, 30, None, COLOR_NEGRO),
    "titulo": (321, 966, 30, None, COLOR_NEGRO),
    "fecha_titulo": (485, 1029, 30, None, COLOR_NEGRO),
    "categoria": (383, 1477, 30, None, COLOR_NEGRO),
    "marca": (326, 1527, 30, None, COLOR_NEGRO),
    "modelo": (338, 1576, 30, None, COLOR_NEGRO),
    "color": (311, 1626, 30, None, COLOR_NEGRO),
    "vin": (469, 1676, 30, None, COLOR_NEGRO),
    "serie": (494, 1729, 30, None, COLOR_NEGRO),
    "motor": (499, 1777, 30, None, COLOR_NEGRO),
    "carroceria": (399, 1827, 30, None, COLOR_NEGRO),
    "potencia": (362, 1877, 30, None, COLOR_NEGRO),
    "form_rod": (397, 1927, 30, None, COLOR_NEGRO),
    "combustible": (425, 1975, 30, None, COLOR_NEGRO),
    "asientos": (390, 2039, 30, None, COLOR_NEGRO),
    "pasajeros": (390, 2088, 30, None, COLOR_NEGRO),
    "ruedas": (390, 2141, 30, None, COLOR_NEGRO),
    "ejes": (390, 2189, 30, None, COLOR_NEGRO),
    "cilindros": (751, 2039, 30, None, COLOR_NEGRO),
    "longitud": (751, 2088, 30, None, COLOR_NEGRO),
    "altura": (751, 2141, 30, None, COLOR_NEGRO),
    "ancho": (751, 2189, 30, None, COLOR_NEGRO),
    "cilindrada": (1242, 2039, 30, None, COLOR_NEGRO),
    "p_bruto": (1242, 2088, 30, None, COLOR_NEGRO),
    "p_neto": (1242, 2141, 30, None, COLOR_NEGRO),
    "carga_util": (1242, 2189, 30, None, COLOR_NEGRO),
    "año_modelo": (1413, 1527, 30, None, COLOR_NEGRO),
    "año_fabricacion": (1413, 1476, 30, None, COLOR_NEGRO), # Ejemplo de coordenada
    "version": (1028, 1927, 30, None, COLOR_NEGRO),
    "numero_tarjeta":(1393, 1396, 30, FUENTE_ARIAL, COLOR_GRISCLARO),
    "placa":(1136, 947, 81, FUENTE_ROBOTOBD, COLOR_NEGRO),
    "placa_anterior": (1235, 1150, 30, None, COLOR_NEGRO) # Ejemplo de coordenada   
}

def generar_imagen_pil(texto_input, modo_azura=False):
    lineas = texto_input.split('\n')
    
    # Detectar presencia de datos clave
    tiene_placa_ant = any("placa_anterior:" in l.lower() and l.split(':', 1)[1].strip() for l in lineas)
    tiene_año_fab = any("año_fabricacion:" in l.lower() and l.split(':', 1)[1].strip() for l in lineas)

    # Selección de fondo: Si modo_azura es True, forzamos TIVE1
    if modo_azura:
        ruta_fondo = FONDO_TIVE1
    elif tiene_placa_ant:
        ruta_fondo = FONDO_TIVE3
    elif tiene_año_fab:
        ruta_fondo = FONDO_TIVE2
    else:
        ruta_fondo = FONDO_TIVE1

    if not os.path.exists(ruta_fondo): 
        print(f"Error: No se encuentra el archivo {ruta_fondo}")
        return None

    img = Image.open(ruta_fondo).convert("RGB")
    draw = ImageDraw.Draw(img)
    for linea in lineas:
        if "foto:" in linea.lower():
            depto_folder = linea.split(':', 1)[1].strip()
            ruta_carpeta = os.path.join(FOLDER_IMAGENES, depto_folder) 
            if os.path.exists(ruta_carpeta) and os.path.isdir(ruta_carpeta):
                archivos = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if archivos:
                    foto_elegida = random.choice(archivos)
                    ruta_foto = os.path.join(ruta_carpeta, foto_elegida)
                    foto_img = Image.open(ruta_foto).convert("RGBA")
                    img.paste(foto_img, COORD_FOTO, foto_img)
    for linea in lineas:
        if ":" in linea:
            partes = linea.split(':', 1)
            etiqueta = partes[0].strip().lower()
            valor_raw = partes[1].strip()
            
            # Si el valor contiene 'tn' o 'mt', no lo pasamos a mayúsculas totalmente
            if any(unit in valor_raw.lower() for unit in ['tn', 'mt']):
                valor = valor_raw # Mantiene el valor como viene del JS (ej: "0.199 tn")
            else:
                valor = valor_raw.upper()
            if etiqueta in CONFIG_CAMPOS and valor.strip() != "":
                x, y, tam, fuente_especifica, color = CONFIG_CAMPOS[etiqueta]
                
                x, y, tam, fuente_especifica, color = CONFIG_CAMPOS[etiqueta]
                ruta_fuente = fuente_especifica if fuente_especifica else FUENTE_GENERAL
                try:
                    fuente = ImageFont.truetype(ruta_fuente, tam)
                    draw.text((x, y), valor, font=fuente, fill=color, anchor="lt")
                except:
                    fuente = ImageFont.truetype(FUENTE_GENERAL, tam)
                    draw.text((x, y), valor, font=fuente, fill=color, anchor="lt")
    return img


def extraer_recorte_pdf(pdf_stream):
    try:
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        pagina = doc[0] 
        
        # --- 1. POSICIÓN (Mueve el recorte sin cambiar su tamaño) ---
        # Aumentar X = Mueve a la derecha | Disminuir X = Mueve a la izquierda
        # Aumentar Y = Baja el recorte | Disminuir Y = Sube el recorte
        x_inicio = 56  # Cambia de 1 en 1 para ajuste fino
        y_inicio = 48 # Cambia de 1 en 1 para ajuste fino
        
        # --- 2. TAMAÑO DE LA VENTANA (No los toques si el tamaño ya te gusta) ---
        # Estos definen qué tan grande es el "cuadro" que arrancas del PDF
        ancho_ventana = 63 
        alto_ventana = 60
        
        # Calculamos el rectángulo final basado en el inicio + el tamaño
        rect = fitz.Rect(x_inicio, y_inicio, x_inicio + ancho_ventana, y_inicio + alto_ventana)
        
        # --- 3. ZOOM VISUAL ---
        # Mantenlo fijo para que el fragmento no cambie de tamaño sobre el TIVE
        zoom = 4.29 
        mat = fitz.Matrix(zoom, zoom)
        
        pix = pagina.get_pixmap(clip=rect, matrix=mat, colorspace=fitz.csRGB)
        img_recorte = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        doc.close()
        return img_recorte
    except Exception as e:
        print(f"Error en ajuste fino: {e}")
        return None
    
@app.route('/', methods=['GET', 'POST'])
def index():
    imagen_base64, texto_previo, depto_previo, pos_guion = None, "", "", "cen"
    edit_az, az_verif, az_fecha, az_tarjeta = "NO", "", "", ""
    
    if request.method == 'POST':
        texto_previo = request.form.get('texto_datos', '')
        depto_previo = request.form.get('depto_nombre', '')
        pos_guion = request.form.get('pos_guion', 'cen')
        
        # Captura de nuevos campos para persistencia
        edit_az = request.form.get('edit_az', 'NO')
        az_verif = request.form.get('az_verif_val', '')
        az_fecha = request.form.get('az_fecha_val', '')
        az_tarjeta = request.form.get('az_tarjeta_val', '')
        
        # 1. Generamos la imagen base con el texto
        modo_azura = (edit_az == "SI")
        img = generar_imagen_pil(texto_previo, modo_azura=modo_azura)
        
        # 2. Si hay un PDF, extraemos el recorte y lo pegamos en la MISMA 'img'
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file and file.filename.endswith('.pdf'):
                # Leer el contenido del archivo
                pdf_data = file.read()
                if pdf_data:
                    recorte = extraer_recorte_pdf(pdf_data)
                    if recorte and img:
                        # Pegamos el recorte en la coordenada definida
                        # Si el recorte tiene transparencia, usa: img.paste(recorte, COORD_PEGADO_PDF, recorte)
                        img.paste(recorte, COORD_PEGADO_PDF)
        
        # 3. Ahora que 'img' tiene el texto Y el recorte del PDF, la mostramos
        if img:
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=90) # Subí la calidad a 90 para que el PDF se vea nítido
            imagen_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
    return render_template('index.html', imagen_preview=imagen_base64, texto=texto_previo, depto_previo=depto_previo, pos_guion=pos_guion)
@app.route('/descargar', methods=['POST'])
def descargar():
    texto = request.form.get('texto_datos', '')
    placa = "S-P"
    # Extraer placa del texto para el nombre del archivo
    for linea in texto.split('\n'):
        if linea.lower().startswith('placa:'):
            placa = linea.split(':')[1].strip().upper()
            break
    
    edit_az = request.form.get('edit_az', 'NO')
    img = generar_imagen_pil(texto, modo_azura=(edit_az == "SI"))
    if img:
        img_io = io.BytesIO()
        img.save(img_io, 'PDF', resolution=300.0)
        img_io.seek(0)
        return send_file(img_io, mimetype='application/pdf', as_attachment=True, download_name=f'TIVE_{placa}.pdf')
    return "Error", 400

if __name__ == '__main__':
    app.run(debug=True)