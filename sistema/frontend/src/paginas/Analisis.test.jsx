// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Analisis from './Analisis.jsx'

function respuesta(datos, ok = true) {
  return { ok, text: async () => JSON.stringify(datos) }
}

function rutaApi(url) {
  const texto = String(url)
  return /^https?:\/\//i.test(texto) ? new URL(texto).pathname + new URL(texto).search : texto
}

const estado = {
  ciclo_id: 10,
  dimensiones: [{
    id: 1,
    codigo: 'D1',
    nombre: 'Gestión',
    indicadores: [{
      id: 2,
      codigo: 'I1',
      nombre: 'Planificación',
      criterios: [{
        id: 3,
        codigo: 'C1',
        codigo_manual: 'M-1',
        nombre: 'Plan aprobado',
        evidencias_clasificadas: 2,
        datos_cuantitativos: true,
        dato_con_respaldo: false,
        tiene_valoracion: true,
        tiene_accion: false,
      }],
    }],
  }],
}

const completitud = {
  ciclo_id: 10,
  criterios_sin_evidencia: [3],
  criterios_cuantitativos_sin_dato: [],
  datos_sin_respaldo: [{ tipo: 'valor_modelo', id: 8, modelo_id: 6, curso: 2024 }],
  modelos_incompletos: [{ modelo_id: 6, numero_modelo: 4, curso: 2024, campos_esperados: 8, campos_presentes: 5 }],
  dimensiones_sin_valoracion: [1],
  debilidades_sin_accion: [4],
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('Pantalla de análisis', () => {
  it('renderiza el árbol dimensión-indicador-criterio con indicadores visuales', async () => {
    vi.stubGlobal('fetch', vi.fn((url) => {
      const ruta = rutaApi(url)
      if (ruta === '/api/ciclos/') {
        return Promise.resolve(respuesta({ results: [{ id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 1 }] }))
      }
      if (ruta === '/api/ciclos/10/estado/') return Promise.resolve(respuesta(estado))
      if (ruta === '/api/ciclos/10/completitud/') return Promise.resolve(respuesta(completitud))
      return Promise.resolve(respuesta({ codigo: 'not_found', mensaje: 'No encontrado.' }, false))
    }))

    render(<Analisis usuario={{ rol: 'administrador_tecnico', carrera: null }} />)

    expect(await screen.findByText(/D1/)).toBeTruthy()
    expect(screen.getByText(/D1/)).toBeTruthy()
    expect(screen.getByText(/C1/)).toBeTruthy()
    expect(screen.getByText('Evidencias: 2')).toBeTruthy()
  })

  it('oculta tipos de aviso vacíos al activar "solo con avisos"', async () => {
    vi.stubGlobal('fetch', vi.fn((url) => {
      const ruta = rutaApi(url)
      if (ruta === '/api/ciclos/') return Promise.resolve(respuesta([{ id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 1 }]))
      if (ruta === '/api/ciclos/10/estado/') return Promise.resolve(respuesta(estado))
      if (ruta === '/api/ciclos/10/completitud/') return Promise.resolve(respuesta(completitud))
      return Promise.resolve(respuesta({}, false))
    }))

    render(<Analisis usuario={{ rol: 'director_carrera', carrera: 1 }} />)
    fireEvent.click(await screen.findByRole('button', { name: 'Completitud' }))
    expect(await screen.findByText('Criterios sin evidencia')).toBeTruthy()
    expect(screen.getByText('M-1 · Plan aprobado')).toBeTruthy()
    expect(screen.getByText('Gestión')).toBeTruthy()
    expect(screen.getByText('Modelo 4 - Curso 2024: Faltan 3 campos')).toBeTruthy()
    expect(screen.getByText('Dato del modelo 6 - Curso 2024 sin evidencia')).toBeTruthy()

    fireEvent.click(screen.getByLabelText('Solo con avisos'))
    expect(screen.queryByText('Criterios cuantitativos sin dato')).toBeNull()
    expect(screen.getByText('Datos sin respaldo')).toBeTruthy()
  })

  it('conecta la comparación y resalta las diferencias devueltas por el endpoint', async () => {
    const fetchMock = vi.fn((url) => {
      const ruta = rutaApi(url)
      if (ruta === '/api/ciclos/') {
        return Promise.resolve(respuesta([
          { id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 1 },
          { id: 11, tipo: 'ordinario', anio_base: 2028, carrera: 1 },
        ]))
      }
      if (ruta === '/api/ciclos/10/estado/') return Promise.resolve(respuesta(estado))
      if (ruta === '/api/ciclos/10/completitud/') return Promise.resolve(respuesta(completitud))
      if (ruta === '/api/comparaciones/?a=10&b=11') {
        return Promise.resolve(respuesta({
          ciclo_a_id: 10,
          ciclo_b_id: 11,
          diferencias_modelos: [{ campo_id: 5, posicion_relativa: 0, valor_a: 1, valor_b: 2 }],
          diferencias_criterios: [],
          diferencias_acciones: [{ debilidad_id: 4, estado_a: 'propuesta', estado_b: 'cumplida', total_a: 1, total_b: 1 }],
        }))
      }
      return Promise.resolve(respuesta({ codigo: 'not_found', mensaje: 'No encontrado.' }, false))
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<Analisis usuario={{ rol: 'administrador_tecnico' }} />)
    await screen.findByRole('heading', { name: 'Estado del ciclo #10' })
    fireEvent.change(screen.getByLabelText('Ciclo'), { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: 'Comparación' }))
    fireEvent.change(screen.getByLabelText('Ciclo A'), { target: { value: '10' } })
    fireEvent.change(screen.getByLabelText('Ciclo B'), { target: { value: '11' } })
    fireEvent.click(screen.getByRole('button', { name: 'Comparar' }))

    expect(await screen.findByRole('heading', { name: 'Diferencias destacadas' })).toBeTruthy()
    expect(screen.getAllByTestId(/diferencia-/).length).toBe(2)
    await waitFor(() => {
      expect(fetchMock.mock.calls.some(([url]) => rutaApi(url).includes('/api/comparaciones/?a=10&b=11'))).toBe(true)
    })
  })

  it('rechaza la pantalla para roles distintos de Administrador y Director', () => {
    render(<Analisis usuario={{ rol: 'miembro' }} />)
    expect(screen.getByText(/Solo el Administrador técnico y el Director de carrera/)).toBeTruthy()
  })
})
