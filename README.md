# Nintendo Switch 2 Monitor

Monitor personal de precios para Nintendo Switch 2 en Chile.

## Reglas

- Consola estándar: alerta a **$550.000 CLP o menos**.
- Bundle: alerta a **$600.000 CLP o menos**.
- Excluye preventas, productos usados/reacondicionados y publicaciones Zelda.
- Envía las alertas por Telegram.
- No repite la misma oferta en cada ejecución.

## Frecuencia

GitHub Actions revisa los precios cada 10 minutos, a los minutos 07, 17, 27, 37, 47 y 57.

> GitHub puede retrasar ocasionalmente los workflows programados. La revisión no es tiempo real al segundo.

## Fuentes iniciales

- Bestmart
- WePlay
- Falabella (venta directa)
- Mercado Libre - Tienda Oficial Nintendo
- PC Factory mediante páginas públicas de seguimiento de precios de TecnoGangas
- Paris
- Ripley
- Lider
- Hites
- ABC

Para estas últimas tiendas se usa SoloTodo como capa de descubrimiento/comparación y se intenta enlazar directamente a la oferta de la tienda.

## Secrets necesarios

En **Settings > Secrets and variables > Actions**:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Prueba manual

En la pestaña **Actions**, abre **Monitor Nintendo Switch 2**, pulsa **Run workflow**, marca
**Enviar solo una notificación de prueba a Telegram** y ejecuta el workflow.


## Alerta grupal Zelda

El mismo bot también monitorea la **Nintendo Switch 2 - The Legend of Zelda 40.º Aniversario** para el grupo de Telegram "Ofertas".

- Sin límite de precio.
- Incluye preventas, reposiciones de stock y publicaciones nuevas.
- No envía al chat privado: va únicamente al grupo.
- Fuentes directas iniciales: Bestmart, WePlay, Mathogames, Santo Games, TodoJuegos y Mercado Libre.
- También intenta descubrir nuevas fichas en Falabella, Ripley, Paris, Lider, Hites y ABC.
- Solo vuelve a avisar cuando una publicación pasa a disponible, cambia de estado o cambia de precio.


## Antispam

El monitor guarda estado en `state.json`. No repite la misma oferta en cada ejecución:
- misma tienda + misma publicación + mismo precio: se avisa una sola vez;
- si deja de cumplir el umbral y más adelante vuelve a entrar en oferta, puede avisarse nuevamente;
- para Zelda, solo se vuelve a avisar si cambia disponibilidad, estado o precio.
