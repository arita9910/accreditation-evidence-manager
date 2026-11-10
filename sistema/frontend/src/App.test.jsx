// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import peticion from './api/cliente'
import { Mensaje } from './componentes'
import App from './App.jsx'

afterEach(() => {
  cleanup()
  localStorage.clear()
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

describe('sesión y administración', () => {
  it('inicia sesión con usuario administrador y muestra el perfil', async () => {
    window.history.pushState({}, '', '/login')
    document.cookie = 'csrftoken=token-login'
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify({
          usuario: {
            id: 7,
            username: 'admin',
            rol: 'administrador_tecnico',
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify({
          id: 7,
          username: 'admin',
          nombre: 'Ana',
          apellidos: 'García',
          email: 'ana@example.com',
          rol: 'administrador_tecnico',
          carrera: null,
          permisos: ['gestionar_usuarios'],
        }),
      })

    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'Secreto123!' } })
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('heading', { name: 'Mi perfil' })).toBeTruthy()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/api\/sesion\/$/), expect.objectContaining({
      method: 'POST',
    }))
  })

  it('oculta acciones de gestión para un director de carrera', async () => {
    window.localStorage.setItem('acuenta.usuario', JSON.stringify({
      id: 12,
      username: 'director',
      rol: 'director_carrera',
    }))
    window.history.pushState({}, '', '/usuarios')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({
        id: 12,
        username: 'director',
        rol: 'director_carrera',
      }),
    }))
    render(<App />)

    expect(await screen.findByText('Solo el administrador técnico puede gestionar usuarios y roles.')).toBeTruthy()
  })

  it('muestra el mensaje de error cuando el backend devuelve 403 en usuarios', async () => {
    window.localStorage.setItem('acuenta.usuario', JSON.stringify({
      id: 4,
      username: 'admin',
      rol: 'administrador_tecnico',
    }))
    window.history.pushState({}, '', '/usuarios')
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        text: async () => JSON.stringify({
          id: 4,
          username: 'admin',
          rol: 'administrador_tecnico',
        }),
      })
      .mockResolvedValueOnce({
        ok: false,
        text: async () => JSON.stringify({
          codigo: 'permission_denied',
          mensaje: 'No tiene permiso para listar usuarios.',
        }),
      }))

    render(<App />)

    expect(await screen.findByText(/No tiene permiso para listar usuarios\./)).toBeTruthy()
  })
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

    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/api\/salud\/$/), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': 'token-de-prueba',
      },
      body: JSON.stringify({ nombre: 'Prueba' }),
      credentials: 'include',
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
