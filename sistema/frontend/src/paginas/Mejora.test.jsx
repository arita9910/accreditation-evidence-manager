// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Mejora from './Mejora.jsx'

function respuesta(datos, ok = true) {
  return {
    ok,
    text: async () => JSON.stringify(datos),
  }
}

function rutaApi(url) {
  const texto = String(url)
  if (/^https?:\/\//i.test(texto)) {
    return new URL(texto).pathname + new URL(texto).search
  }
  return texto
}

function prepararFetchBase({ cicloEstado = 'abierto' } = {}) {
  const fetchMock = vi.fn((url, opciones = {}) => {
    const ruta = rutaApi(url)
    const metodo = (opciones.method || 'GET').toUpperCase()

    if (ruta === '/api/ciclos/' && metodo === 'GET') {
      return Promise.resolve(respuesta({
        results: [{ id: 10, tipo: 'acreditación', carrera: 3, anio_base: 2026, estado: cicloEstado }],
      }))
    }

    if (ruta === '/api/ciclos/10/valoraciones/?tipo=debilidad' && metodo === 'GET') {
      return Promise.resolve(respuesta({
        results: [{ id: 501, tipo: 'debilidad', texto: 'No hay rúbricas consistentes.' }],
      }))
    }

    if (ruta === '/api/usuarios/?carrera=3' && metodo === 'GET') {
      return Promise.resolve(respuesta([
        { id: 9, username: 'director', nombre: 'Dirección', apellidos: 'Carrera', carrera: 3 },
        { id: 12, username: 'responsable', nombre: 'Ana', apellidos: 'Torres', carrera: 3 },
      ]))
    }

    if (ruta === '/api/ciclos/10/plan/' && metodo === 'GET') {
      return Promise.resolve(respuesta({
        id: 77,
        ciclo: 10,
        estado: 'borrador',
        aprobado_por: null,
      }))
    }

    if (ruta === '/api/planes/77/acciones/' && metodo === 'GET') {
      return Promise.resolve(respuesta([
        {
          id: 301,
          plan: 77,
          debilidad: 501,
          descripcion: 'Definir rúbricas compartidas',
          responsable: 9,
          responsable_nombre: 'Dirección Carrera',
          fecha_limite: '2020-01-01',
          estado: 'en_curso',
          valoracion_resultado: '',
        },
      ]))
    }

    if (ruta === '/api/acciones/301/seguimientos/' && metodo === 'GET') {
      return Promise.resolve(respuesta([
        { id: 901, accion: 301, fecha: '2026-02-01T00:00:00Z', avance: 30, nota: 'Primer avance', registrado_por: 9 },
      ]))
    }

    if (ruta === '/api/ciclos/10/plan-anterior/' && metodo === 'GET') {
      return Promise.resolve(respuesta({
        plan: { id: 41, ciclo: 9, estado: 'cerrado', aprobado_por: 4 },
        acciones: [{ id: 201, descripcion: 'Acción cerrada del ciclo previo', estado: 'cumplida' }],
      }))
    }

    if (ruta === '/api/planes/77/acciones/' && metodo === 'POST') {
      return Promise.resolve(respuesta({ id: 400 }, true))
    }

    if (ruta === '/api/acciones/301/seguimientos/' && metodo === 'POST') {
      return Promise.resolve(respuesta({ id: 990, accion: 301, avance: 45, nota: 'Seguimiento manual', registrado_por: 9 }, true))
    }

    if (ruta === '/api/acciones/301/' && metodo === 'PATCH') {
      return Promise.resolve(respuesta({ id: 301 }, true))
    }

    if (ruta === '/api/acciones/301/' && metodo === 'DELETE') {
      return Promise.resolve(respuesta({}, true))
    }

    if (ruta === '/api/planes/77/' && metodo === 'PATCH') {
      return Promise.resolve(respuesta({
        id: 77,
        ciclo: 10,
        estado: 'aprobado',
        aprobado_por: 9,
        aprobado_por_nombre: 'Dirección Carrera',
      }, true))
    }

    return Promise.resolve(respuesta({ codigo: 'not_found', mensaje: 'No encontrado.' }, false))
  })

  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('Pantalla de mejora', () => {
  it('muestra plan actual y anterior, resaltando acciones vencidas', async () => {
    prepararFetchBase()

    render(
      <MemoryRouter>
        <Mejora usuario={{ id: 9, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Plan de mejora' })).toBeTruthy()
    expect(await screen.findByText('Acción cerrada del ciclo previo')).toBeTruthy()
    expect((await screen.findAllByText('Definir rúbricas compartidas')).length).toBeGreaterThanOrEqual(1)
    expect((await screen.findAllByText('Dirección Carrera')).length).toBeGreaterThan(0)
    expect(screen.getByText('Vencida')).toBeTruthy()
  })

  it('habilita el registro solo con todos los datos y envía el responsable seleccionado', async () => {
    const fetchMock = prepararFetchBase()

    render(
      <MemoryRouter>
        <Mejora usuario={{ id: 9, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Plan de mejora' })).toBeTruthy()
    expect(await screen.findByText('Vencida')).toBeTruthy()
    expect(await screen.findByLabelText('Responsable')).toBeTruthy()

    const boton = screen.getByRole('button', { name: 'Registrar acción' })
    expect(boton.disabled).toBe(true)
    fireEvent.change(screen.getByLabelText('Descripción'), { target: { value: 'Nueva acción para el ciclo' } })
    fireEvent.change(screen.getByLabelText('Responsable'), { target: { value: '12' } })
    fireEvent.change(screen.getByLabelText('Fecha límite'), { target: { value: '2026-12-31' } })
    expect(boton.disabled).toBe(true)
    fireEvent.change(screen.getByLabelText('Debilidad de origen'), { target: { value: '501' } })
    expect(boton.disabled).toBe(false)
    fireEvent.click(boton)

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(([url, opciones = {}]) => rutaApi(url) === '/api/planes/77/acciones/' && (opciones.method || '').toUpperCase() === 'POST')
      expect(llamada).toBeTruthy()
      const [, opciones] = llamada
      expect(JSON.parse(opciones.body)).toEqual({
        debilidad: 501,
        descripcion: 'Nueva acción para el ciclo',
        responsable: 12,
        fecha_limite: '2026-12-31',
      })
    }, 15000)
    expect(screen.getByRole('option', { name: 'Ana Torres' })).toBeTruthy()
  })

  it('permite registrar seguimiento y refresca el historial', async () => {
    const fetchMock = prepararFetchBase()

    render(
      <MemoryRouter>
        <Mejora usuario={{ id: 9, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Plan de mejora' })).toBeTruthy()
    expect(await screen.findByText(/30% · Primer avance/)).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Avance (%)'), { target: { value: '45' } })
    fireEvent.change(screen.getByLabelText('Nota'), { target: { value: 'Seguimiento manual' } })
    fireEvent.click(screen.getByRole('button', { name: 'Registrar seguimiento' }))

    expect(await screen.findByText('Seguimiento registrado correctamente.')).toBeTruthy()

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(([url, opciones = {}]) => rutaApi(url) === '/api/acciones/301/seguimientos/' && (opciones.method || '').toUpperCase() === 'POST')
      expect(llamada).toBeTruthy()
      const [, opciones] = llamada
      expect(JSON.parse(opciones.body)).toEqual({ avance: 45, nota: 'Seguimiento manual' })
    }, 15000)
  })

  it('evita registrar cambios cuando el ciclo está cerrado', async () => {
    const fetchMock = prepararFetchBase({ cicloEstado: 'cerrado' })

    render(
      <MemoryRouter>
        <Mejora usuario={{ id: 9, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Plan de mejora' })).toBeTruthy()
    expect(await screen.findByText('El ciclo está cerrado. Solo se permite la consulta del plan.')).toBeTruthy()
    const botonRegistrar = await screen.findByRole('button', { name: 'Registrar acción' })
    expect(botonRegistrar.disabled).toBe(true)
    expect(
      fetchMock.mock.calls.some(([url, opciones = {}]) => rutaApi(url) === '/api/planes/77/acciones/' && (opciones.method || '').toUpperCase() === 'POST'),
    ).toBe(false)
  })

  it('permite editar y eliminar acciones con botones en la tabla', async () => {
    const fetchMock = prepararFetchBase()

    render(
      <MemoryRouter>
        <Mejora usuario={{ id: 9, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Plan de mejora' })).toBeTruthy()
    expect(await screen.findByText('Vencida')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    expect(await screen.findByRole('heading', { name: 'Editar acción' })).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Descripción'), { target: { value: 'Acción actualizada' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    await waitFor(() => {
      const llamadaPatch = fetchMock.mock.calls.find(([url, opciones = {}]) => rutaApi(url) === '/api/acciones/301/' && (opciones.method || '').toUpperCase() === 'PATCH')
      expect(llamadaPatch).toBeTruthy()
    }, 15000)

    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }))

    await waitFor(() => {
      const llamadaDelete = fetchMock.mock.calls.find(([url, opciones = {}]) => rutaApi(url) === '/api/acciones/301/' && (opciones.method || '').toUpperCase() === 'DELETE')
      expect(llamadaDelete).toBeTruthy()
    }, 15000)
  })

  it('permite editar el estado del plan', async () => {
    const fetchMock = prepararFetchBase()

    render(
      <MemoryRouter>
        <Mejora usuario={{ id: 9, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Plan de mejora' })).toBeTruthy()
    expect(await screen.findByText('Vencida')).toBeTruthy()
    const botonEditarPlan = screen.queryByRole('button', { name: 'Editar plan' })
    if (botonEditarPlan) {
      fireEvent.click(botonEditarPlan)
    }
    fireEvent.change(screen.getByLabelText('Estado del plan'), { target: { value: 'aprobado' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar plan' }))

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(([url, opciones = {}]) => rutaApi(url) === '/api/planes/77/' && (opciones.method || '').toUpperCase() === 'PATCH')
      expect(llamada).toBeTruthy()
    }, 15000)
  })
})
