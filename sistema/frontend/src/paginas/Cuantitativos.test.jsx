// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Cuantitativos from './Cuantitativos.jsx'

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

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('Pantalla de cuantitativos', () => {
  it('valida no negativos en tabla y calcula porcentajes', async () => {
    const fetchMock = vi.fn((url, opciones = {}) => {
      const ruta = rutaApi(url)
      const metodo = (opciones.method || 'GET').toUpperCase()
      if (ruta === '/api/ciclos/' && metodo === 'GET') {
        return Promise.resolve(respuesta({
          results: [{ id: 10, tipo: 'ordinario', anio_base: 2026, curso_final: 2025 }],
        }))
      }
      if (ruta === '/api/catalogo/modelos/' && metodo === 'GET') {
        return Promise.resolve(respuesta([{
          numero: 1,
          nombre: 'Resumen',
          campos: [{ id: 11, fila: 1, columna: 1, tipo_valor: 'porcentaje', orden: 1 }],
        }]))
      }
      if (ruta === '/api/catalogo/' && metodo === 'GET') {
        return Promise.resolve(respuesta({
          dimensiones: [{
            indicadores: [{
              criterios: [{
                codigo: '1.1.1',
                texto: 'Cobertura',
                tipo_dato: 'cuantitativo',
                modelos: [],
                requisitos_por_categoria: [{ categoria: 'calificada', texto: 'Cobertura mínima de referencia.' }],
              }],
            }],
          }],
        }))
      }
      if (ruta.startsWith('/api/ciclos/10/modelos/1/valores/') && metodo === 'GET') {
        return Promise.resolve(respuesta({
          celdas: [{ campo: 11, valor: null, numerador: null, denominador: null }],
        }))
      }
      if (ruta === '/api/ciclos/10/criterios/1.1.1/valor/' && metodo === 'GET') {
        return Promise.resolve(respuesta({
          valor: { valor: null, numerador: null, denominador: null, curso: 2025, unidad: '', observacion: '' },
        }))
      }
      if (ruta === '/api/ciclos/10/datos/sin-respaldo/' && metodo === 'GET') {
        return Promise.resolve(respuesta({ datos: [] }))
      }
      return Promise.resolve(respuesta({ codigo: 'not_found', mensaje: 'No encontrado.' }, false))
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<Cuantitativos usuario={{ id: 1, rol: 'director_carrera' }} />)

    expect(await screen.findByRole('heading', { name: 'Datos cuantitativos' })).toBeTruthy()
    expect(await screen.findByText('1,1')).toBeTruthy()

    fireEvent.change(screen.getByRole('textbox', { name: 'numerador-1-1' }), { target: { value: '2' } })
    fireEvent.change(screen.getByRole('textbox', { name: 'denominador-1-1' }), { target: { value: '5' } })
    expect((await screen.findAllByText('40.0')).length).toBeGreaterThanOrEqual(1)

    fireEvent.change(screen.getByRole('textbox', { name: 'valor-1-1' }), { target: { value: '-1' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar modelo' }))

    expect(await screen.findByText('El campo (1,1) no puede ser negativo.')).toBeTruthy()
    expect(fetchMock.mock.calls.some(([, opciones = {}]) => (opciones.method || '').toUpperCase() === 'PUT')).toBe(false)
  })

  it('muestra referencia de guía y valida no negativos en criterio', async () => {
    const fetchMock = vi.fn((url, opciones = {}) => {
      const ruta = rutaApi(url)
      const metodo = (opciones.method || 'GET').toUpperCase()
      if (ruta === '/api/ciclos/' && metodo === 'GET') {
        return Promise.resolve(respuesta({
          results: [{ id: 10, tipo: 'ordinario', anio_base: 2026, curso_final: 2025 }],
        }))
      }
      if (ruta === '/api/catalogo/modelos/' && metodo === 'GET') {
        return Promise.resolve(respuesta([{
          numero: 1,
          nombre: 'Resumen',
          campos: [{ id: 11, fila: 1, columna: 1, tipo_valor: 'entero', orden: 1 }],
        }]))
      }
      if (ruta === '/api/catalogo/' && metodo === 'GET') {
        return Promise.resolve(respuesta({
          dimensiones: [{
            indicadores: [{
              criterios: [{
                codigo: '1.1.1',
                texto: 'Cobertura',
                tipo_dato: 'cuantitativo',
                modelos: [],
                requisitos_por_categoria: [{ categoria: 'calificada', texto: 'Referencia en guía.' }],
              }],
            }],
          }],
        }))
      }
      if (ruta.startsWith('/api/ciclos/10/modelos/1/valores/') && metodo === 'GET') {
        return Promise.resolve(respuesta({
          celdas: [{ campo: 11, valor: null, numerador: null, denominador: null }],
        }))
      }
      if (ruta === '/api/ciclos/10/criterios/1.1.1/valor/' && metodo === 'GET') {
        return Promise.resolve(respuesta({
          valor: { valor: null, numerador: null, denominador: null, curso: 2025, unidad: '', observacion: '' },
        }))
      }
      if (ruta === '/api/ciclos/10/datos/sin-respaldo/' && metodo === 'GET') {
        return Promise.resolve(respuesta({ datos: [] }))
      }
      return Promise.resolve(respuesta({ codigo: 'not_found', mensaje: 'No encontrado.' }, false))
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<Cuantitativos usuario={{ id: 1, rol: 'director_carrera' }} />)

    expect(await screen.findByText(/Referencia de la Guía: Referencia en guía\./)).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Valor'), { target: { value: '-3' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar criterio' }))

    expect(await screen.findByText('El campo valor del criterio no puede ser negativo.')).toBeTruthy()
    expect(fetchMock.mock.calls.some(([, opciones = {}]) => (opciones.method || '').toUpperCase() === 'PUT')).toBe(false)
  })
})
