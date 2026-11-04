async function peticion(url, opciones = {}) {
  const config = {
    ...opciones,
    credentials: 'same-origin',
    headers: {
      ...(opciones.headers || {}),
    },
  }

  const metodo = (opciones.method || 'GET').toUpperCase()
  const necesitaCsrf = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(metodo)

  if (necesitaCsrf) {
    const csrfToken = document.cookie
      .split('; ')
      .find((entrada) => entrada.startsWith('csrftoken='))
      ?.split('=')[1]

    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken
    }
  }

  const respuesta = await fetch(url, config)
  const cuerpo = await respuesta.text()
  const datos = cuerpo ? JSON.parse(cuerpo) : {}

  if (!respuesta.ok) {
    const codigo = datos?.codigo || 'error'
    const mensaje = datos?.mensaje || 'No se pudo completar la solicitud.'
    const detalle = datos?.detalle || datos
    throw new Error(`${codigo}: ${mensaje}${detalle ? ` - ${JSON.stringify(detalle)}` : ''}`)
  }

  return datos
}

export default peticion
