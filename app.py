import os
import io
import base64
import random
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# --- CONFIGURACIÓN DE RUTAS ---
FOLDER_FUENTES = "fuentes"
FOLDER_IMAGENES = "imagenes"
IMG_FONDO = os.path.join("static", "tive.png") 

# Definición de fuentes
FUENTE_GENERAL = os.path.join(FOLDER_FUENTES, "phagspa.ttf")
FUENTE_ARIAL = os.path.join(FOLDER_FUENTES, "arial.ttf")
FUENTE_ARIALBD = os.path.join(FOLDER_FUENTES, "arialbd.ttf")
FUENTE_ROBOTOBD = os.path.join(FOLDER_FUENTES, "robotobd.ttf")

COLOR_GRIS_73 = (130, 130, 130)  
COLOR_NEGRO = (0, 0, 0)
COLOR_GRISCLARO = (203, 203, 203)
COORD_FOTO = (1159, 2245) 

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
    "año_modelo": (1405, 1527, 30, None, COLOR_NEGRO),
    "version": (1028, 1927, 30, None, COLOR_NEGRO),
    "numero_tarjeta":(1393, 1396, 30, FUENTE_ARIAL, COLOR_GRISCLARO),
    "placa":(1136, 947, 81, FUENTE_ROBOTOBD, COLOR_NEGRO)
}

def generar_imagen_pil(texto_input):
    if not os.path.exists(IMG_FONDO): return None
    img = Image.open(IMG_FONDO).convert("RGB")
    draw = ImageDraw.Draw(img)
    lineas = texto_input.split('\n')
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
            valor = partes[1].strip().upper()
            if etiqueta in CONFIG_CAMPOS:
                x, y, tam, fuente_especifica, color = CONFIG_CAMPOS[etiqueta]
                ruta_fuente = fuente_especifica if fuente_especifica else FUENTE_GENERAL
                try:
                    fuente = ImageFont.truetype(ruta_fuente, tam)
                    draw.text((x, y), valor, font=fuente, fill=color, anchor="lt")
                except:
                    fuente = ImageFont.truetype(FUENTE_GENERAL, tam)
                    draw.text((x, y), valor, font=fuente, fill=color, anchor="lt")
    return img

@app.route('/', methods=['GET', 'POST'])
def index():
    imagen_base64, texto_previo, depto_previo, pos_guion = None, "", "", "cen"
    if request.method == 'POST':
        texto_previo = request.form.get('texto_datos', '')
        depto_previo = request.form.get('depto_nombre', '')
        pos_guion = request.form.get('pos_guion', 'cen')
        img = generar_imagen_pil(texto_previo)
        if img:
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=75)
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
    
    img = generar_imagen_pil(texto)
    if img:
        img_io = io.BytesIO()
        img.save(img_io, 'PDF', resolution=300.0)
        img_io.seek(0)
        return send_file(img_io, mimetype='application/pdf', as_attachment=True, download_name=f'TIVE_{placa}.pdf')
    return "Error", 400

if __name__ == '__main__':
    app.run(debug=True)