const API_BASE_URL = '/api';

function construirUrl(url) {
  if (/^https?:\/\//i.test(url)) {
    return url
  }

  const ruta = url.startsWith('/') ? url : `/${url}`
  const rutaSinPrefijoApi = ruta === '/api' ? '' : (ruta.startsWith('/api/') ? ruta.slice(4) : ruta)
  return `${API_BASE_URL}${rutaSinPrefijoApi}`
}

async function peticion(url, opciones = {}) {
  const config = {
    ...opciones,
    credentials: 'include',
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

  const respuesta = await fetch(construirUrl(url), config)
  const cuerpo = await respuesta.text()
  let datos = {}

  if (cuerpo) {
    try {
      datos = JSON.parse(cuerpo)
    } catch {
      throw new Error(`respuesta_invalida: El servidor devolvió contenido no JSON (${respuesta.status}).`)
    }
  }

  if (!respuesta.ok) {
    const codigo = datos?.codigo || 'error'
    const mensaje = datos?.mensaje || 'No se pudo completar la solicitud.'
    const detalle = datos?.detalle || datos
    throw new Error(`${codigo}: ${mensaje}${detalle ? ` - ${JSON.stringify(detalle)}` : ''}`)
  }

  return datos
}

export default peticion
