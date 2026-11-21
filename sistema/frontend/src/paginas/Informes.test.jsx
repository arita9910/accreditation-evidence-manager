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

  it('la vista del par evaluador es solo lectura y reutiliza el árbol de evidencias', async () => {
    const fetchMock = vi.fn(async (url) => {
      const ruta = rutaApi(url)
      if (ruta === '/api/ciclos/') {
        return respuestaJson([{ id: 10, tipo: 'ordinario', anio_base: 2026 }])
      }
      if (ruta === '/api/ciclos/10/expediente/') {
        return respuestaJson({
          ciclo: 10,
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
    expect(screen.queryByRole('button', { name: /editar|crear|eliminar|guardar/i })).toBeNull()
    expect(screen.getByText(/Vista de solo lectura/)).toBeTruthy()
  })
})
