// @vitest-environment jsdom

import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import peticion from './api/cliente'
import { Mensaje } from './componentes'
import App from './App.jsx'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
  document.cookie = 'csrftoken=; Max-Age=0'
})

describe('App', () => {
  it('muestra el catálogo normativo', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({
        version: { nombre: 'SEA-CU 2025' },
        dimensiones: [],
      }),
    }))

    render(<App />)

    expect(await screen.findByRole('heading', {
      name: 'Catálogo normativo SEA-CU 2025',
    })).toBeTruthy()
  }, 30000)
})

describe('Mensaje', () => {
  it('muestra mensajes de error con el estilo adecuado', () => {
    render(<Mensaje tipo="error" titulo="Error">No se pudo guardar</Mensaje>)

    const alert = screen.getAllByRole('alert').at(-1)
    expect(alert.textContent).toContain('Error')
    expect(alert.textContent).toContain('No se pudo guardar')
  })
})

describe('cliente API', () => {
  it('envía la cookie CSRF en las solicitudes POST', async () => {
    document.cookie = 'csrftoken=token-de-prueba'
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      text: async () => '{"estado":"ok"}',
    })
    vi.stubGlobal('fetch', fetchMock)

    await peticion('/api/salud/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre: 'Prueba' }),
    })

    expect(fetchMock).toHaveBeenCalledWith('/api/salud/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': 'token-de-prueba',
      },
      body: JSON.stringify({ nombre: 'Prueba' }),
      credentials: 'same-origin',
    })
  })

  it('presenta el mensaje común de error usando Mensaje', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      text: async () => JSON.stringify({
        codigo: 'no_autorizado',
        mensaje: 'No se pudo guardar',
        detalle: { campo: 'nombre' },
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    let error
    try {
      await peticion('/api/recurso/')
    } catch (errorRecibido) {
      error = errorRecibido
    }

    render(<Mensaje tipo="error">{error.message}</Mensaje>)

    expect(screen.getByRole('alert').textContent).toContain('No se pudo guardar')
  })
})
