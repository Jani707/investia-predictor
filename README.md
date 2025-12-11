# 📈 InvestIA Predictor

Sistema de predicción de inversiones con Inteligencia Artificial.

---

## 🚀 INICIO RÁPIDO (Copia y Pega)

### Entrenar los Modelos
Abre Terminal y copia estos comandos **uno por uno**:

```bash
cd .
source venv/bin/activate
cd backend
python train.py --all
```

⏱️ Espera 20-30 minutos. Verás el progreso en pantalla.

---

### Iniciar el Sistema (Local)

**Solo necesitas una terminal:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

*   El Backend iniciará en `http://localhost:8000`
*   El Frontend ahora se sirve automáticamente en la misma dirección: `http://localhost:8000`

---

### 🚀 Despliegue en Render

Este proyecto ahora está configurado para desplegarse como un **único Web Service**.

1.  **Build Command:** `pip install -r backend/requirements.txt`
2.  **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3.  **Root Directory:** `.` (La raíz del repo)

¡No necesitas desplegar el frontend por separado!

---

## � Configuración de Notificaciones (Correo)

Para recibir alertas de oportunidades de inversión, debes configurar tu correo Gmail:

1.  **Obtener Contraseña de Aplicación (App Password)**:
    *   Ve a tu [Cuenta de Google](https://myaccount.google.com/).
    *   Busca "Contraseñas de aplicaciones" (debes tener la verificación en 2 pasos activada).
    *   Crea una nueva para "Correo" y "Mac" (o el nombre que quieras).
    *   Copia la contraseña de 16 caracteres que te dan.

2.  **Configurar en el Sistema**:
    *   Abre el archivo `backend/app/config.py`.
    *   Busca la sección `EMAIL_CONFIG` (cerca del final).
    *   Reemplaza los valores:
        ```python
        "sender": "tu_correo@gmail.com",
        "password": "tu_contraseña_de_aplicación_aquí",
        ```
    *   Guarda el archivo.

3.  **Probar**:
    *   Asegúrate de que el backend esté corriendo.
    *   Visita `http://localhost:8000/api/test-email` para enviar un correo de prueba.

---

## �📊 Entendiendo las Predicciones

### Recomendaciones

| Ves | Significa | Qué Hacer |
|-----|-----------|-----------|
| 🟢 **COMPRAR** | Se espera que suba +2% | Considera comprar |
| 🟡 **MANTENER** | Sin cambios significativos | No hagas nada |
| 🔴 **VENDER** | Se espera que baje -2% | Considera vender |

### Confianza del Modelo

| Nivel | Significado |
|-------|-------------|
| 70-100% | ✅ Predicción confiable |
| 40-70% | ⚠️ Usar con precaución |
| 0-40% | ❌ Poco confiable |

---

## 💰 Los 6 ETFs Disponibles

| Símbolo | Qué Es | Riesgo |
|---------|--------|--------|
| **VOO** | 500 empresas más grandes de EE.UU. | Bajo |
| **VTI** | Todo el mercado de EE.UU. | Bajo |
| **BND** | Bonos (deuda segura) | Muy Bajo |
| **SCHD** | Empresas que pagan dividendos | Bajo |
| **VNQ** | Bienes raíces | Medio |
| **GLD** | Oro | Bajo |

---

## 💳 Dónde Invertir (Chile)

| Plataforma | Para | Mínimo |
|------------|------|--------|
| [Fintual](https://fintual.cl) | Principiantes | $1.000 CLP |
| [Racional](https://racional.cl) | ETFs directos | $50.000 CLP |
| [eToro](https://etoro.com) | Fácil de usar | $200 USD |

---

## 🎯 Estrategia Simple para Empezar

1. **Invierte poco** - Solo dinero que no necesites
2. **Diversifica** - No todo en un solo ETF
3. **Revisa semanal** - Abre el dashboard cada semana
4. **Sigue la confianza** - Solo actúa con confianza >60%

### Ejemplo de Distribución
```
40% VOO (Mercado general)
30% BND (Seguridad)
20% SCHD (Dividendos)
10% GLD (Oro)
```

---

## ❓ Problemas Comunes

**"No carga el dashboard"**
→ Verifica que ambas Terminales estén corriendo

**"No hay predicciones"**
→ Entrena los modelos: `python train.py --all`

**"Error de conexión"**
→ Cierra todo y vuelve a iniciar los servidores

---

## ⚠️ Aviso Legal

Este sistema es **solo educativo**. Las predicciones NO garantizan resultados. 
Toda inversión tiene riesgos. Nunca inviertas dinero que no puedas perder.

---

*InvestIA Predictor v1.0*
