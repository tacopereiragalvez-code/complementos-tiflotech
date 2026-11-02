from flask import Flask, request, render_template_string
import requests
import base64
import json
from datetime import datetime

app = Flask(__name__)

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
GITHUB_TOKEN = "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"  # <--- PON TU TOKEN AQUÍ
GITHUB_REPO = "tacopereiragalvez-code/complementos-tiflotech"
# ==========================================

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
        h2 { text-align: center; color: #4CAF50; margin-bottom: 20px; }
        .tabs { display: flex; margin-bottom: 20px; }
        .tab { flex: 1; padding: 10px; text-align: center; cursor: pointer; background: #333; border-radius: 5px 5px 0 0; }
        .tab.active { background: #4CAF50; font-weight: bold; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        input, textarea, select, button { width: 100%; padding: 10px; margin-top: 10px; border-radius: 5px; border: none; box-sizing: border-box; }
        input, textarea, select { background: #333; color: white; }
        button { background: #4CAF50; color: white; font-weight: bold; cursor: pointer; margin-top: 20px; }
        button:hover { background: #45a049; }
        .mensaje { margin-top: 15px; padding: 10px; border-radius: 5px; text-align: center; }
        .exito { background: #2e7d32; }
        .error { background: #c62828; }
        label { display: block; margin-top: 15px; color: #aaa; }
    </style>
</head>
<body>
    <div class="container">
        <h2>TifloTech Admin</h2>
        
        <div class="tabs">
            <div class="tab active" onclick="cambiarTab(0)">Subir Nuevo</div>
            <div class="tab" onclick="cambiarTab(1)">Editar Existente</div>
        </div>

        <!-- PESTAÑA 1: SUBIR NUEVO -->
        <div id="tab0" class="tab-content active">
            <form method="POST" action="/subir" enctype="multipart/form-data">
                <label>Nombre del archivo (ej. TifloTech TV Player.ppk):</label>
                <input type="text" name="nombre_archivo" required placeholder="Nombre exacto con .ppk">
                
                <label>Descripción:</label>
                <textarea name="descripcion" rows="3" required></textarea>
                
                <label>Archivo .ppk:</label>
                <input type="file" name="archivo" accept=".ppk" required>
                
                <button type="submit">Subir a GitHub</button>
            </form>
        </div>

        <!-- PESTAÑA 2: EDITAR EXISTENTE -->
        <div id="tab1" class="tab-content">
            <form method="POST" action="/editar" enctype="multipart/form-data">
                <label>Selecciona el complemento a editar:</label>
                <select name="nombre_archivo" id="selector" onchange="cargarDatos()">
                    <option value="">-- Selecciona un complemento --</option>
                    {% for key, value in info.items() %}
                    <option value="{{ key }}" data-desc="{{ value.descripcion }}" data-fecha="{{ value.fecha }}">{{ key }}</option>
                    {% endfor %}
                </select>

                <label>Nueva Descripción:</label>
                <textarea name="descripcion" id="edit-desc" rows="3" required></textarea>

                <label>Nueva Fecha (opcional):</label>
                <input type="date" name="fecha" id="edit-fecha">

                <label>Reemplazar archivo .ppk (opcional):</label>
                <input type="file" name="archivo" accept=".ppk">

                <button type="submit">Guardar Cambios</button>
            </form>
        </div>

        {% if mensaje %}
        <div class="mensaje {{ 'exito' if exito else 'error' }}">{{ mensaje }}</div>
        {% endif %}
    </div>

    <script>
        function cambiarTab(n) {
            document.querySelectorAll('.tab').forEach((t, i) => t.classList.toggle('active', i === n));
            document.querySelectorAll('.tab-content').forEach((c, i) => c.classList.toggle('active', i === n));
        }

        function cargarDatos() {
            var select = document.getElementById("selector");
            var opcion = select.options[select.selectedIndex];
            document.getElementById("edit-desc").value = opcion.getAttribute("data-desc") || "";
            document.getElementById("edit-fecha").value = opcion.getAttribute("data-fecha") || "";
        }
    </script>
</body>
</html>
"""

def get_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def obtener_info_actual():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/info.json"
    res = requests.get(url, headers=get_headers())
    if res.status_code == 200:
        data = res.json()
        sha = data['sha']
        contenido = json.loads(base64.b64decode(data['content']).decode('utf-8'))
        return sha, contenido
    return None, {}

def guardar_info_json(contenido, sha, mensaje_commit):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/info.json"
    nuevo_contenido_b64 = base64.b64encode(json.dumps(contenido, indent=2, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    payload = {
        "message": mensaje_commit,
        "content": nuevo_contenido_b64
    }
    if sha:
        payload["sha"] = sha
    res_put = requests.put(url, headers=get_headers(), json=payload)
    return res_put.status_code in [200, 201]

def subir_archivo_github(nombre_archivo, archivo):
    contenido_archivo = archivo.read()
    contenido_b64 = base64.b64encode(contenido_archivo).decode('utf-8')
    url_archivo = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{nombre_archivo}"
    
    res_check = requests.get(url_archivo, headers=get_headers())
    sha_archivo = res_check.json().get('sha') if res_check.status_code == 200 else None

    payload = {
        "message": f"Subir/Actualizar {nombre_archivo}",
        "content": contenido_b64
    }
    if sha_archivo:
        payload["sha"] = sha_archivo

    res_subida = requests.put(url_archivo, headers=get_headers(), json=payload)
    return res_subida.status_code in [200, 201]

@app.route('/')
def index():
    _, info = obtener_info_actual()
    return render_template_string(HTML_PANEL, info=info)

@app.route('/subir', methods=['POST'])
def subir():
    nombre_archivo = request.form.get('nombre_archivo', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    archivo = request.files.get('archivo')

    if not nombre_archivo or not archivo or not nombre_archivo.endswith('.ppk'):
        _, info = obtener_info_actual()
        return render_template_string(HTML_PANEL, info=info, mensaje="Error: Datos inválidos o no es un .ppk", exito=False)

    if not subir_archivo_github(nombre_archivo, archivo):
        _, info = obtener_info_actual()
        return render_template_string(HTML_PANEL, info=info, mensaje="Error al subir el archivo a GitHub.", exito=False)

    sha, info = obtener_info_actual()
    info[nombre_archivo] = {
        "descripcion": descripcion,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "descargas": info.get(nombre_archivo, {}).get("descargas", 0)
    }

    if guardar_info_json(info, sha, f"Subir {nombre_archivo}"):
        return render_template_string(HTML_PANEL, info=info, mensaje=f"¡{nombre_archivo} subido con éxito!", exito=True)
    else:
        return render_template_string(HTML_PANEL, info=info, mensaje="Archivo subido, pero falló el JSON.", exito=False)

@app.route('/editar', methods=['POST'])
def editar():
    nombre_archivo = request.form.get('nombre_archivo', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    fecha = request.form.get('fecha', '').strip()
    archivo = request.files.get('archivo')

    if not nombre_archivo:
        _, info = obtener_info_actual()
        return render_template_string(HTML_PANEL, info=info, mensaje="Error: Selecciona un complemento.", exito=False)

    # Si el usuario subió un archivo nuevo, lo reemplazamos
    if archivo and archivo.filename != '':
        if not subir_archivo_github(nombre_archivo, archivo):
            _, info = obtener_info_actual()
            return render_template_string(HTML_PANEL, info=info, mensaje="Error al actualizar el archivo en GitHub.", exito=False)

    sha, info = obtener_info_actual()
    if nombre_archivo in info:
        info[nombre_archivo]["descripcion"] = descripcion
        if fecha:
            info[nombre_archivo]["fecha"] = fecha
    else:
        _, info = obtener_info_actual()
        return render_template_string(HTML_PANEL, info=info, mensaje="Error: El complemento no existe.", exito=False)

    if guardar_info_json(info, sha, f"Editar {nombre_archivo}"):
        return render_template_string(HTML_PANEL, info=info, mensaje=f"¡{nombre_archivo} actualizado con éxito!", exito=True)
    else:
        return render_template_string(HTML_PANEL, info=info, mensaje="Error al guardar los cambios.", exito=False)