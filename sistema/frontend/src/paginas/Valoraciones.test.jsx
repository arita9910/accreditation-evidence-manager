// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Valoraciones from './Valoraciones.jsx'
import { formatearAsistentePorcentaje } from './valoracionesAsistente'

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

function prepararFetch() {
  const fetchMock = vi.fn((url, opciones = {}) => {
    const ruta = rutaApi(url)
    const metodo = (opciones.method || 'GET').toUpperCase()

    if (ruta === '/api/ciclos/' && metodo === 'GET') {
      return Promise.resolve(respuesta({
        results: [{ id: 10, tipo: 'ordinario', anio_base: 2026 }],
      }))
    }

    if (/^\/api\/ciclos\/10\/valoraciones\/catalogo\/?$/.test(ruta) && metodo === 'GET') {
      return Promise.resolve(respuesta({
        dimensiones: [{
          id: 1,
          codigo: '1',
          nombre: 'Planificación',
          indicadores: [{
            codigo: '1.1',
            texto: 'Indicador',
            criterios: [{ id: 101, codigo: '1.1.1', texto: 'Criterio 1' }],
          }],
        }],
      }))
    }

    if (/^\/api\/ciclos\/10\/valoraciones\/?$/.test(ruta) && metodo === 'GET') {
      return Promise.resolve(respuesta({
        results: [
          { id: 500, ciclo: 10, dimension: 1, tipo: 'fortaleza', texto: 'Fortaleza inicial', criterios: [101], evidencias: [200] },
          { id: 501, ciclo: 10, dimension: 1, tipo: 'debilidad', texto: 'Debilidad inicial', criterios: [101], evidencias: [200] },
        ],
      }))
    }

    if (/^\/api\/evidencias\/\?ciclo=10$/.test(ruta) && metodo === 'GET') {
      return Promise.resolve(respuesta({
        results: [
          { id: 200, titulo: 'Acta clasificada', clasificaciones: [{ id: 1, criterio: 101 }] },
          { id: 201, titulo: 'Documento sin clasificar', clasificaciones: [] },
        ],
      }))
    }

    if (/^\/api\/ciclos\/10\/valoraciones\/?$/.test(ruta) && metodo === 'POST') {
      return Promise.resolve(respuesta({ id: 999 }, true))
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

describe('Pantalla de valoraciones', () => {
  it('renderiza editor por dimensión con listas por tipo y tipo visual por defecto', async () => {
    prepararFetch()

    render(
      <MemoryRouter>
        <Valoraciones usuario={{ id: 1, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Valoraciones cualitativas' })).toBeTruthy()
    expect(await screen.findByText('Fortaleza inicial')).toBeTruthy()
    expect(await screen.findByText('Debilidad inicial')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Fortaleza' }).className).toContain('btn-primary')
    expect(screen.getByRole('button', { name: 'Debilidad' }).className).toContain('btn-outline-primary')
    expect(screen.getByText('Acta clasificada')).toBeTruthy()
    expect(screen.queryByText('Documento sin clasificar')).toBeNull()
  }, 15000)

  it('formatea el asistente de porcentaje con coma decimal exacta', () => {
    expect(formatearAsistentePorcentaje('86,2', 19, 23)).toBe('86,2 % (19/23)')
  })

  it('calcula porcentaje automático de solo lectura e inserta el formato en el texto', async () => {
    prepararFetch()

    render(
      <MemoryRouter>
        <Valoraciones usuario={{ id: 1, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Valoraciones cualitativas' })).toBeTruthy()

    const campoPorcentaje = screen.getByLabelText('Porcentaje (%)')
    const campoNumerador = screen.getByLabelText('Numerador')
    const campoDenominador = screen.getByLabelText('Denominador')
    const campoTexto = screen.getByLabelText('Texto')

    expect(campoPorcentaje.readOnly).toBe(true)
    fireEvent.change(campoNumerador, { target: { value: '19' } })
    fireEvent.change(campoDenominador, { target: { value: '23' } })
    expect(campoPorcentaje.value).toBe('82,6')

    fireEvent.click(screen.getByRole('button', { name: 'Insertar porcentaje' }))
    expect(campoTexto.value).toContain('82,6 % (19/23)')
  }, 15000)

  it('muestra error y vacía porcentaje cuando denominador es cero o numerador supera denominador', async () => {
    prepararFetch()

    render(
      <MemoryRouter>
        <Valoraciones usuario={{ id: 1, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Valoraciones cualitativas' })).toBeTruthy()

    const campoPorcentaje = screen.getByLabelText('Porcentaje (%)')
    const campoNumerador = screen.getByLabelText('Numerador')
    const campoDenominador = screen.getByLabelText('Denominador')

    fireEvent.change(campoNumerador, { target: { value: '5' } })
    fireEvent.change(campoDenominador, { target: { value: '0' } })
    expect(campoPorcentaje.value).toBe('')
    expect(screen.getByText('Debe indicar un denominador entero mayor que cero.')).toBeTruthy()

    fireEvent.change(campoDenominador, { target: { value: '4' } })
    expect(campoPorcentaje.value).toBe('')
    expect(screen.getByText('El numerador no puede ser mayor que el denominador.')).toBeTruthy()
  }, 15000)

  it('valida que no se guarde sin evidencias clasificadas seleccionadas', async () => {
    const fetchMock = prepararFetch()

    render(
      <MemoryRouter>
        <Valoraciones usuario={{ id: 1, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Valoraciones cualitativas' })).toBeTruthy()
    expect(await screen.findByRole('option', { name: /1\s+·\s+Planificación/ })).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Dimensión'), { target: { value: '1' } })
    fireEvent.change(screen.getByLabelText('Texto'), { target: { value: 'Nueva valoración con sustento' } })
    fireEvent.click(await screen.findByLabelText('1.1.1 · Criterio 1'))
    fireEvent.click(screen.getByRole('button', { name: 'Registrar valoración' }))

    expect(await screen.findByText('Debe seleccionar al menos una evidencia clasificada del ciclo.')).toBeTruthy()
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([url, opciones = {}]) => rutaApi(url) === '/api/ciclos/10/valoraciones/' && (opciones.method || '').toUpperCase() === 'POST'),
      ).toBe(false)
    }, 15000)
  })
})
