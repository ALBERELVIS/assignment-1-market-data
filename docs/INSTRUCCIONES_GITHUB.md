# 📤 Cómo Subir el Proyecto a GitHub (SIN usar Git)

Esta guía te explica cómo subir tu proyecto completo a GitHub usando **solo la interfaz web**, sin necesidad de instalar Git en tu computadora.

---

## 🎯 Paso a Paso

### Paso 1: Preparar los Archivos

1. **Asegúrate de tener todos los archivos del proyecto en una carpeta**
   - La carpeta debe contener:
     - `src/` (con todos los archivos .py)
     - `requirements.txt`
     - `README.md`
     - `.gitignore`
     - `example_usage.py`
     - `INSTRUCCIONES_GITHUB.md` (este archivo)

2. **Verifica que no falte nada:**
   ```
   Tu carpeta debería verse así:
   
   📁 Tu-Proyecto/
      📁 src/
         ├── __init__.py
         ├── data_extractor.py
         ├── price_series.py
         ├── portfolio.py
         ├── data_cleaning.py
         └── main.py
      ├── requirements.txt
      ├── README.md
      ├── .gitignore
      ├── example_usage.py
      └── INSTRUCCIONES_GITHUB.md
   ```

---

### Paso 2: Crear Repositorio en GitHub (si no existe)

1. **Ve a GitHub.com e inicia sesión**

2. **Haz clic en el botón "+" (arriba a la derecha) → "New repository"**

3. **Configura el repositorio:**
   - **Repository name**: `analisis-bursatil` (o el nombre que prefieras)
   - **Description**: "Sistema de análisis bursátil - Proyecto Master"
   - **Visibility**: 
     - ⚪ **Public** (si quieres que sea público)
     - ⚫ **Private** (si quieres que sea privado - recomendado para entregas académicas)
   - **NO marques** "Initialize this repository with a README" (ya tienes uno)
   - **NO selecciones** ninguna licencia por ahora

4. **Haz clic en "Create repository"**

---

### Paso 3: Subir Archivos (Método 1: Interfaz Web)

**Opción A: Usando el botón "uploading an existing file"**

1. **En la página de tu repositorio recién creado**, verás un mensaje que dice:
   > "Quick setup — if you've done this kind of thing before"
   
   **O busca el botón "uploading an existing file"** (si ya tienes archivos)

2. **Haz clic en "uploading an existing file"**

3. **Arrastra y suelta TODA la carpeta del proyecto** O haz clic en "choose your files" y selecciona todos los archivos

4. **En la parte inferior**, escribe:
   - **Commit message**: "Initial commit - Proyecto completo de análisis bursátil"
   - **Descripción (opcional)**: "Primera versión del proyecto con todos los módulos"

5. **Haz clic en "Commit changes"**

---

### Paso 3: Subir Archivos (Método 2: GitHub Desktop)

Si prefieres usar una interfaz gráfica más amigable:

1. **Descarga GitHub Desktop** desde [desktop.github.com](https://desktop.github.com/)

2. **Instala GitHub Desktop** (no necesitas instalar Git por separado)

3. **Inicia sesión** en GitHub Desktop con tu cuenta

4. **File → Add Local Repository**
   - Busca la carpeta de tu proyecto
   - Haz clic en "Add repository"

5. **En la parte superior**, verás tu repositorio local
   - En la pestaña "Changes", verás todos los archivos nuevos
   - Escribe un mensaje de commit: "Initial commit - Proyecto completo"

6. **Haz clic en "Commit to main"**

7. **Haz clic en "Publish repository"** (si es la primera vez) O "Push origin" (si ya existe)

---

### Paso 4: Verificar que Todo Esté Subido

1. **Refresca la página de tu repositorio en GitHub**

2. **Verifica que veas:**
   - ✅ Carpeta `src/` con todos los archivos .py
   - ✅ `requirements.txt`
   - ✅ `README.md` (que se muestra automáticamente en la página principal)
   - ✅ `.gitignore`
   - ✅ `example_usage.py`

3. **Haz clic en `README.md`** para verificar que se vea bien

---

### Paso 5: Compartir el Link

1. **Copia la URL de tu repositorio** desde la barra de direcciones del navegador
   - Ejemplo: `https://github.com/tu-usuario/analisis-bursatil`

2. **Guarda esta URL en un archivo de texto** para entregarlo a tus profesores

3. **Asegúrate de que el repositorio sea:**
   - **Público** (si quieren acceder sin autenticación), O
   - **Privado pero con acceso compartido** (si quieres mantenerlo privado)

---

## 📝 Notas Importantes

### Si el Repositorio es Privado

Si creaste el repositorio como **privado**, tus profesores necesitarán acceso:

1. **Ve a Settings → Collaborators**
2. **Haz clic en "Add people"**
3. **Ingresa el email/usuario de GitHub de tu profesor**
4. **Haz clic en "Add [nombre] to this repository"**

### Archivos que NO Debes Subir

El archivo `.gitignore` ya está configurado para **NO subir**:
- Carpetas `venv/` o `env/` (entornos virtuales)
- Archivos `.pyc` (compilados de Python)
- Carpetas `__pycache__/`
- Archivos temporales

**Si accidentalmente subiste algo que no deberías:**
1. Ve al archivo en GitHub
2. Haz clic en el ícono de lápiz (editar)
3. Elimina el contenido
4. Haz commit

---

## 🎓 Para la Entrega

**Lo que debes entregar:**

1. **Link al repositorio de GitHub** (en un archivo .txt)
   - Ejemplo contenido del archivo:
   ```
   Link al repositorio de GitHub:
   https://github.com/tu-usuario/analisis-bursatil
   ```

2. **Asegúrate de que:**
   - ✅ El repositorio esté completo
   - ✅ El README.md sea visible y esté bien formateado
   - ✅ Todos los archivos estén en la carpeta `src/`
   - ✅ El `requirements.txt` esté presente
   - ✅ El código sea ejecutable (puedes probarlo antes)

---

## 🔍 Verificación Final

Antes de entregar, verifica:

- [ ] Todos los archivos están en GitHub
- [ ] El README.md se ve bien en GitHub
- [ ] La estructura de carpetas es correcta
- [ ] El link del repositorio funciona
- [ ] El repositorio es accesible (público o con permisos)

---

## ❓ Problemas Comunes

### "No puedo ver el archivo .gitignore"

- Los archivos que empiezan con punto (`.`) están ocultos por defecto
- En GitHub, deberías poder verlo normalmente
- Si no aparece, puedes crearlo directamente en GitHub: "Add file" → "Create new file" → nombre: `.gitignore`

### "El README.md no se muestra"

- Asegúrate de que el archivo se llame exactamente `README.md` (mayúsculas y minúsculas)
- Debe estar en la **raíz** del repositorio (no dentro de una carpeta)

### "No puedo subir muchos archivos a la vez"

- GitHub web tiene límites, pero con este proyecto no debería haber problema
- Si es necesario, sube los archivos en grupos (primero `src/`, luego los demás)

---

## ✅ ¡Listo!

Una vez que hayas subido todo y verificado, tu proyecto estará listo para entregar.

**Recuerda:** El link de tu repositorio es lo único que necesitas compartir con tus profesores.

---

**¡Éxito con tu entrega! 🚀**

