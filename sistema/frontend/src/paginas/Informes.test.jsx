// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import InformeTextos from './InformeTextos.jsx'
import InformeGeneracion from './InformeGeneracion.jsx'
import ExpedienteEvaluador from './ExpedienteEvaluador.jsx'

function respuestaJson(datos) {
  return {
    ok: true,
    text: async () => JSON.stringify(datos),
  }
}

function rutaApi(url) {
  return new URL(String(url), 'http://testserver').pathname
}

beforeEach(() => {
  document.cookie = 'csrftoken=token-prueba'
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('pantallas del módulo de informes', () => {
  it('carga y guarda textos cualitativos y muestra ciclo cerrado', async () => {
    const fetchMock = vi.fn(async (url, opciones = {}) => {
      const ruta = rutaApi(url)
      const metodo = (opciones.method || 'GET').toUpperCase()
      if (ruta === '/api/ciclos/' && metodo === 'GET') {
        return respuestaJson([{ id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 3, estado: 'abierto' }])
      }
      if (ruta === '/api/ciclos/10/informe/textos/' && metodo === 'GET') {
        return respuestaJson({
          ciclo: 10,
          secciones: [{ seccion: 'caracterizacion', descripcion: 'Caracterización', contenido: 'Texto inicial' }],
        })
      }
      if (ruta === '/api/ciclos/10/informe/textos/caracterizacion/' && metodo === 'PUT') {
        return respuestaJson({ seccion: 'caracterizacion', contenido: 'Texto actualizado' })
      }
      return respuestaJson({})
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<InformeTextos usuario={{ rol: 'director_carrera', carrera: 3 }} />)
    const area = await screen.findByLabelText('Caracterización')
    expect(area.value).toBe('Texto inicial')
    fireEvent.change(area, { target: { value: 'Texto actualizado' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar texto' }))
    expect(await screen.findByText('Texto guardado correctamente.')).toBeTruthy()
  })

  it('deshabilita el editor cuando el ciclo está cerrado', async () => {
    const fetchMock = vi.fn(async (url) => {
      const ruta = rutaApi(url)
      if (ruta === '/api/ciclos/') {
        return respuestaJson([{ id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 3, estado: 'cerrado' }])
      }
      if (ruta === '/api/ciclos/10/informe/textos/') {
        return respuestaJson({
          ciclo: 10,
          secciones: [{ seccion: 'caracterizacion', descripcion: 'Caracterización', contenido: 'Texto cerrado' }],
        })
      }
      return respuestaJson({})
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<InformeTextos usuario={{ rol: 'director_carrera', carrera: 3 }} />)
    expect(await screen.findByText('El ciclo está cerrado. Los textos cualitativos no se pueden modificar.')).toBeTruthy()
    expect((await screen.findByLabelText('Caracterización')).disabled).toBe(true)
  })

  it('mantiene el botón de generar con avisos de completitud y muestra el historial', async () => {
    const fetchMock = vi.fn(async (url, opciones = {}) => {
      const ruta = rutaApi(url)
      const metodo = (opciones.method || 'GET').toUpperCase()
      if (ruta === '/api/ciclos/' && metodo === 'GET') {
        return respuestaJson([{ id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 3, estado: 'abierto' }])
      }
      if (ruta === '/api/ciclos/10/completitud/' && metodo === 'GET') {
        return respuestaJson({ avisos: ['Criterios sin evidencia'] })
      }
      if (ruta === '/api/ciclos/10/informe/versiones/' && metodo === 'GET') {
        return respuestaJson({ ciclo: 10, versiones: [{ id: 7, numero: 1, paginas: 20, metodo_conteo: 'estimado' }] })
      }
      if (ruta === '/api/ciclos/10/informe/generar/' && metodo === 'POST') {
        return respuestaJson({ id: 8, numero: 2, paginas: 21, metodo_conteo: 'estimado' })
      }
      return respuestaJson({})
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<InformeGeneracion usuario={{ rol: 'director_carrera', carrera: 3 }} />)
    expect(await screen.findByText('Criterios sin evidencia')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Generar informe' }).disabled).toBe(false)
    expect(await screen.findByText('v1')).toBeTruthy()
  })

  it('formatea los avisos estructurados y las debilidades sin acción', async () => {
    const fetchMock = vi.fn(async (url) => {
      const ruta = rutaApi(url)
      if (ruta === '/api/ciclos/') {
        return respuestaJson([{ id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 3, estado: 'abierto' }])
      }
      if (ruta === '/api/ciclos/10/completitud/') {
        return respuestaJson({
          datos_sin_respaldo: [{ tipo: 'valor_modelo', modelo_id: 1, curso: 2024 }],
          debilidades_sin_accion: [],
        })
      }
      if (ruta === '/api/ciclos/10/informe/versiones/') {
        return respuestaJson({ ciclo: 10, versiones: [] })
      }
      return respuestaJson({})
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<InformeGeneracion usuario={{ rol: 'director_carrera', carrera: 3 }} />)

    expect(await screen.findByText('Dato del modelo 1 - Curso 2024 sin evidencia')).toBeTruthy()
    expect(screen.getByText('No hay debilidades pendientes por resolver')).toBeTruthy()
    expect(screen.queryByText(/\[object Object\]/)).toBeNull()
  })

  it('muestra las debilidades sin acción como números', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url) => {
      const ruta = rutaApi(url)
      if (ruta === '/api/ciclos/') {
        return respuestaJson([{ id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 3, estado: 'abierto' }])
      }
      if (ruta === '/api/ciclos/10/completitud/') {
        return respuestaJson({ datos_sin_respaldo: [], debilidades_sin_accion: [4] })
      }
      if (ruta === '/api/ciclos/10/informe/versiones/') {
        return respuestaJson({ ciclo: 10, versiones: [] })
      }
      return respuestaJson({})
    }))

    render(<InformeGeneracion usuario={{ rol: 'director_carrera', carrera: 3 }} />)

    expect((await screen.findByText(/debilidades_sin_accion:/)).closest('li').textContent).toBe('debilidades_sin_accion: 4')
  })

  it('muestra listas extensas de completitud en formato simple', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url) => {
      const ruta = rutaApi(url)
      if (ruta === '/api/ciclos/') {
        return respuestaJson([{ id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 3, estado: 'abierto' }])
      }
      if (ruta === '/api/ciclos/10/completitud/') {
        return respuestaJson({
          criterios_sin_evidencia: Array.from({ length: 60 }, (_, indice) => indice + 1),
          criterios_cuantitativos_sin_dato: [1, 2, 3, 4, 5],
          modelos_incompletos: Array.from({ length: 4 }, (_, indice) => ({
            modelo_id: indice + 1,
            campos_esperados: 8,
            campos_presentes: 5,
          })),
          dimensiones_sin_valoracion: [1, 2, 3],
          debilidades_sin_accion: [4, 5, 6],
        })
      }
      if (ruta === '/api/ciclos/10/informe/versiones/') {
        return respuestaJson({ ciclo: 10, versiones: [] })
      }
      return respuestaJson({})
    }))

    render(<InformeGeneracion usuario={{ rol: 'director_carrera', carrera: 3 }} />)

    expect((await screen.findByText(/criterios_sin_evidencia:/)).closest('li').textContent).toBe(`criterios_sin_evidencia: ${Array.from({ length: 60 }, (_, indice) => indice + 1).join(', ')}`)
    expect(screen.getByText(/criterios_cuantitativos_sin_dato:/).closest('li').textContent).toBe('criterios_cuantitativos_sin_dato: 1, 2, 3, 4, 5')
    expect(screen.getByText(/dimensiones_sin_valoracion:/).closest('li').textContent).toBe('dimensiones_sin_valoracion: 1, 2, 3')
    expect(screen.getByText(/debilidades_sin_accion:/).closest('li').textContent).toBe('debilidades_sin_accion: 4, 5, 6')
    expect(screen.queryByText(/modelos_incompletos:/)).toBeNull()
    expect(screen.queryByText(/\.{3} y \d+ más/)).toBeNull()
  })

  it('la vista del par evaluador es solo lectura y reutiliza el árbol de evidencias', async () => {
    const fetchMock = vi.fn(async (url) => {
      const ruta = rutaApi(url)
      if (ruta === '/api/ciclos/') {
        return respuestaJson([{ id: 10, tipo: 'ordinario', anio_base: 2026 }])
      }
      if (ruta === '/api/ciclos/10/expediente/') {
        return respuestaJson({
          ciclo: 10,
          dimensiones: [{
            id: 1,
            codigo: 'D1',
            nombre: 'Dimensión de prueba',
            indicadores: [{
              id: 2,
              codigo: 'I1',
              texto: 'Indicador de prueba',
              criterios: [{
                id: 101,
                codigo: 'D1-I1-C1',
                texto: 'Criterio de prueba',
                valoraciones: [
                  { tipo: 'fortaleza', texto: 'Fortaleza cualitativa' },
                  { tipo: 'debilidad', texto: 'Debilidad cualitativa' },
                ],
                fortalezas: ['Fortaleza cualitativa'],
                debilidades: ['Debilidad cualitativa'],
              }],
            }],
          }],
          evidencias: [{
            id: 2,
            tipo_evidencia: 5,
            titulo: 'Acta de prueba',
            descripcion: 'Evidencia disponible',
            clasificaciones: [{ id: 1, criterio: 101 }],
            ficheros: [{ id: 3, nombre_original: 'acta.pdf' }],
          }],
        })
      }
      return respuestaJson({})
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<ExpedienteEvaluador usuario={{ rol: 'par_evaluador' }} />)
    expect(await screen.findByText('Acta de prueba')).toBeTruthy()
    expect(await screen.findByText('Fortaleza:')).toBeTruthy()
    expect(await screen.findByText('Debilidad:')).toBeTruthy()
    expect(screen.getByText('Fortaleza cualitativa')).toBeTruthy()
    expect(screen.getByText('Debilidad cualitativa')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /editar|crear|eliminar|guardar/i })).toBeNull()
    expect(screen.getByText(/Vista de solo lectura/)).toBeTruthy()
  })
})
