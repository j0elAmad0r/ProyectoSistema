# ProgSistemas — Intérprete de Lenguaje Personalizado

Un intérprete y compilador de un lenguaje de programación educativo, con editor visual basado en React y backend FastAPI.

## Características

- **Lexer, Parser e Intérprete** completo escrito en Python
- **Backend FastAPI** para ejecutar código remoto
- **Frontend React + Vite** con editor Monaco y Tailwind CSS
- **Soporte para**: variables, funciones, condicionales, bucles, listas, diccionarios, operadores lógicos
- **Mensajes de error** amigables y localizados en español

## Inicio Rápido

### Opción 1: Script Automático (Recomendado)

**Windows PowerShell:**
```powershell
.\setup.ps1
```

Esto instala dependencias Python, npm, levanta el backend y frontend automáticamente.

---

### Opción 2: Configuración Manual

#### 1. Backend (Python)

```powershell
# Crea el entorno virtual
python -m venv .venv

# Activa el entorno
.\.venv\Scripts\Activate.ps1

# Instala dependencias
pip install -r requirements.txt

# Ejecuta el servidor
python app.py
```

El backend estará disponible en `http://127.0.0.1:8000`

#### 2. Frontend (React + Vite)

En una **nueva terminal**:

```powershell
cd frontend

# Instala dependencias (primera vez)
npm install

# Inicia el servidor de desarrollo
npm run dev
```

El frontend estará disponible en `http://127.0.0.1:5173`

---

### Uso

1. Abre `http://127.0.0.1:5173` en tu navegador
2. Escribe código en el editor
3. Pulsa **Run** para ejecutar
4. Los resultados aparecen en la consola de salida

#### Ejemplo de Código

```text
x = 10
y = 20
if (x < y) {
    print("x es menor que y")
}

lista = [1, 2, 3, 4, 5]
resultado = 10 / 2
print(resultado)
```

---

## Estructura del Proyecto

```
ProgSistemas/
├── inicio.py           # Lexer, Parser, Intérprete, Compilador
├── app.py              # Backend FastAPI
├── requirements.txt    # Dependencias Python
├── frontend/           # Aplicación React
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── ...
└── README.md           # Este archivo
```
