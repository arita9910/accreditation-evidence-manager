// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Ciclos from './Ciclos.jsx'

function respuesta(datos, ok = true) {
  return {
    ok,
    text: async () => JSON.stringify(datos),
  }
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

function prepararFetch({
  carreras = [],
  ciclos = [],
  versiones = [],
  asignaciones = [],
} = {}) {
  const fetchMock = vi.fn((url, opciones = {}) => {
    const urlTexto = String(url)

    if (urlTexto === '/api/carreras/' && !opciones.method) {
      return Promise.resolve(respuesta({ results: carreras }))
    }
    if (urlTexto === '/api/ciclos/' && !opciones.method) {
      return Promise.resolve(respuesta({ results: ciclos }))
    }
    if (urlTexto === '/api/catalogo/versiones/' && !opciones.method) {
      return Promise.resolve(respuesta(versiones))
    }
    if (urlTexto.endsWith('/asignaciones/') && !opciones.method) {
      return Promise.resolve(respuesta({ results: asignaciones }))
    }

    return Promise.resolve(respuesta({ codigo: 'not_found', mensaje: 'No encontrado.' }, false))
  })

  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('Pantallas de ciclos', () => {
  it('valida campos requeridos del formulario de apertura y muestra aviso de cinco cursos', async () => {
    prepararFetch({
      carreras: [{ id: 1, nombre: 'Ingeniería de Software', activa: true }],
      ciclos: [],
      versiones: [{ id: 7, nombre: 'SEA-CU 2026' }],
    })

    render(
      <MemoryRouter>
        <Ciclos />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Abrir ciclo' })).toBeTruthy()
    expect(screen.getByText(/cinco cursos consecutivos/)).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: 'Abrir ciclo' }))

    expect(await screen.findByText('Debe seleccionar una carrera.')).toBeTruthy()
    expect(screen.getByText('Debe indicar el tipo de ciclo.')).toBeTruthy()
    expect(screen.getByText('Debe indicar el año base.')).toBeTruthy()
    expect(screen.getByText('Debe indicar el curso inicial.')).toBeTruthy()
    expect(screen.getByText('Debe indicar la versión normativa.')).toBeTruthy()
  })

  it('renderiza la tabla dimensión x usuario con los datos de asignaciones', async () => {
    prepararFetch({
      carreras: [{ id: 1, nombre: 'Ingeniería de Software', activa: true }],
      ciclos: [{ id: 10, carrera: 1, tipo: 'ordinario', anio_base: 2026, curso_inicial: 2021, curso_final: 2025, estado: 'abierto' }],
      versiones: [{ id: 7, nombre: 'SEA-CU 2026' }],
      asignaciones: [
        { id: 100, ciclo: 10, usuario: 1, dimension: 3 },
        { id: 101, ciclo: 10, usuario: 2, dimension: 3 },
        { id: 102, ciclo: 10, usuario: 2, dimension: 4 },
      ],
    })

    render(
      <MemoryRouter>
        <Ciclos />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Asignación dimensión × usuario')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Ciclo abierto'), { target: { value: '10' } })

    const encabezado = await screen.findByRole('columnheader', { name: /Dimensión/ })
    const tabla = encabezado.closest('table')
    expect(tabla).toBeTruthy()
    const contenido = within(tabla)
    expect(contenido.getByText('Usuario #1')).toBeTruthy()
    expect(contenido.getByText('Usuario #2')).toBeTruthy()
    expect(contenido.getByText('Dimensión #3')).toBeTruthy()
    expect(contenido.getByText('Dimensión #4')).toBeTruthy()
  })
})
