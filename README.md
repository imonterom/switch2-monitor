# Nintendo Switch 2 Monitor

Monitor personal de precios para Nintendo Switch 2 en Chile.

## Reglas

- Consola estándar: alerta a **$550.000 CLP o menos**.
- Bundle: alerta a **$600.000 CLP o menos**.
- Excluye preventas, productos usados/reacondicionados y publicaciones Zelda.
- Envía las alertas por Telegram.
- No repite la misma oferta en cada ejecución.

## Frecuencia

GitHub Actions revisa los precios dos veces por hora, a los minutos 07 y 37.

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
