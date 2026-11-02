from flask import Flask, request, render_template_string, redirect, url_for
import requests
import base64
import json

app = Flask(__name__)

# ==========================================
# ⚙️ CONFIGURACIÓN (¡CÁMBIALO AQUÍ!)
# ==========================================
GITHUB_TOKEN = "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"  # Necesitas un Token con permisos de 'repo'
GITHUB_REPO = "tacopereiragalvez-code/complementos-tiflotech"
# ==========================================

# HTML del panel web (Puedes personalizar el diseño)
HTML_PANEL = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TifloTech Admin</title>
    <style>
        body { font-family: sans-serif; background-color: #121212; color: white; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 10px; }
        h2 { text-align: center; color: #4CAF50; }
        input, textarea, button { width: 100%; padding: 10px; margin-top: 10px; border-radius: 5px; border: none; box-sizing: border-box; }
        input, textarea { background: #333; color: white; }
        button { background: #4CAF50; color: white; font-weight: bold; cursor: pointer; }
        button:hover { background: #45a049; }
        .mensaje { margin-top: 15px; padding: 10px; border-radius: 5px; text-align: center; }
        .exito { background: #2e7d32; }
        .error { background: #c62828; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Subir Complemento .ppk</h2>
        <form method="POST" action="/subir" enctype="multipart/form-data">
            <label>Nombre del archivo (ej. TifloTech TV Player.ppk):</label>
            <input type="text" name="nombre_archivo" required placeholder="Nombre exacto con .ppk">
            
            <label>Descripción:</label>
            <textarea name="descripcion" rows="3" required></textarea>
            
            <label>Archivo .ppk:</label>
            <input type="file" name="archivo" accept=".ppk" required>
            
            <button type="submit">Subir a GitHub</button>
        </form>
        {% if mensaje %}
        <div class="mensaje {{ 'exito' if exito else 'error' }}">{{ mensaje }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

def get_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def actualizar_info_json(nombre_archivo, descripcion):
    """Lee el info.json de GitHub, lo actualiza y lo vuelve a subir."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/info.json"
    res = requests.get(url, headers=get_headers())
    
    if res.status_code == 200:
        data = res.json()
        sha = data['sha']
        contenido = json.loads(base64.b64decode(data['content']).decode('utf-8'))
    else:
        sha = None
        contenido = {}

    # Actualizar o crear la entrada
    contenido[nombre_archivo] = {
        "descripcion": descripcion,
        "fecha": "2026-06-14", # Puedes usar datetime.now().strftime("%Y-%m-%d") si importas datetime
        "descargas": contenido.get(nombre_archivo, {}).get("descargas", 0)
    }

    # Convertir a Base64 para GitHub
    nuevo_contenido_b64 = base64.b64encode(json.dumps(contenido, indent=2, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": f"Actualizar info de {nombre_archivo}",
        "content": nuevo_contenido_b64
    }
    if sha:
        payload["sha"] = sha

    res_put = requests.put(url, headers=get_headers(), json=payload)
    return res_put.status_code in [200, 201]

@app.route('/')
def index():
    return render_template_string(HTML_PANEL)

@app.route('/subir', methods=['POST'])
def subir():
    nombre_archivo = request.form.get('nombre_archivo', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    archivo = request.files.get('archivo')

    if not nombre_archivo or not archivo or not nombre_archivo.endswith('.ppk'):
        return render_template_string(HTML_PANEL, mensaje="Error: Datos inválidos o no es un .ppk", exito=False)

    # 1. Subir el archivo .ppk a GitHub
    contenido_archivo = archivo.read()
    contenido_b64 = base64.b64encode(contenido_archivo).decode('utf-8')
    url_archivo = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{nombre_archivo}"
    
    # Verificar si el archivo ya existe para obtener su SHA
    res_check = requests.get(url_archivo, headers=get_headers())
    sha_archivo = res_check.json().get('sha') if res_check.status_code == 200 else None

    payload_archivo = {
        "message": f"Subir/Actualizar {nombre_archivo}",
        "content": contenido_b64
    }
    if sha_archivo:
        payload_archivo["sha"] = sha_archivo

    res_subida = requests.put(url_archivo, headers=get_headers(), json=payload_archivo)
    
    if res_subida.status_code not in [200, 201]:
        return render_template_string(HTML_PANEL, mensaje=f"Error al subir archivo: {res_subida.text}", exito=False)

    # 2. Actualizar info.json con la descripción
    exito_info = actualizar_info_json(nombre_archivo, descripcion)
    
    if exito_info:
        return render_template_string(HTML_PANEL, mensaje=f"¡{nombre_archivo} subido y descrito con éxito!", exito=True)
    else:
        return render_template_string(HTML_PANEL, mensaje="Archivo subido, pero falló la actualización del JSON.", exito=False)

# Vercel necesita que la app se llame 'app' para funcionar
