# 🧠 Guía de Entrenamiento y Actualización de Modelos

Esta guía te explica cómo "enseñarle" cosas nuevas a tu Inteligencia Artificial (entrenar modelos) en tu computadora y subir ese conocimiento a la nube.

## 📋 Prerrequisitos

Asegúrate de tener tu entorno virtual activado en tu terminal:

```bash
source venv/bin/activate
```

## 🚀 Paso 1: Entrenar los Modelos (En tu Mac)

El entrenamiento requiere mucha potencia, por eso lo hacemos en tu Mac y no en el servidor gratuito.

1.  Abre tu terminal en la carpeta del proyecto.
2.  Ejecuta el script de entrenamiento:

```bash
cd backend
python train.py
```

**¿Qué hará esto?**
*   Descargará los últimos datos de precios de Yahoo Finance.
*   Entrenará un modelo LSTM para cada activo configurado (VOO, AAPL, etc.).
*   Guardará los "cerebros" entrenados (archivos `.keras`) en la carpeta `backend/saved_models/`.
*   Generará métricas de precisión (JSON) para saber qué tan confiable es cada modelo.

*Este proceso puede tardar varios minutos dependiendo de cuántos activos tengas.*

## ☁️ Paso 2: Subir los Modelos a GitHub

Una vez que el entrenamiento termine, verás archivos nuevos en `backend/saved_models/`. Necesitamos subirlos para que Render los vea.

1.  Vuelve a la raíz del proyecto:
    ```bash
    cd ..
    ```

2.  Dile a Git que incluya los nuevos modelos (normalmente están ignorados, así que usaremos `-f` si es necesario, o asegurarnos de que `.gitignore` no los bloquee):

    ```bash
    git add backend/saved_models/*.keras
    git add backend/saved_models/*.json
    ```
    *(Nota: Si Git se queja de archivos grandes, asegúrate de que pesen menos de 100MB. Los modelos de este proyecto suelen ser pequeños).*

3.  Guarda los cambios:
    ```bash
    git commit -m "Update: Modelos re-entrenados con datos recientes"
    ```

4.  Súbelos a la nube:
    ```bash
    git push
    ```

## 🔄 Paso 3: Actualización Automática en Render

¡Aquí viene la magia! ✨

1.  En cuanto haces `git push`, **Render detecta el cambio automáticamente**.
2.  Render iniciará un nuevo "Deploy" (despliegue).
3.  Descargará tu código actualizado junto con los nuevos modelos `.keras`.
4.  Reiniciará el servidor.

**⚠️ Nota Importante sobre el Plan Gratuito:**
Actualmente, hemos desactivado la carga de modelos en Render para que el servidor gratuito no se colapse (ya que `TensorFlow` usa mucha memoria).
*   **Si estás en el Plan Gratuito:** El servidor seguirá usando el "Sistema Matemático" (RSI) aunque subas los modelos.
*   **Si mejoras al Plan Starter ($7/mes):** Podremos reactivar `TensorFlow` en el archivo `requirements.txt` y el servidor empezará a usar estos modelos que acabas de subir para hacer predicciones de IA reales.

## 🧪 Cómo probarlo localmente

Antes de subir nada, puedes ver las predicciones de tus nuevos modelos en tu propia computadora:

```bash
# Estando en la carpeta backend/
python ml/predictor.py
```

Esto imprimirá en la consola las predicciones para un activo de prueba (ej: VOO), confirmando que el modelo funciona.
