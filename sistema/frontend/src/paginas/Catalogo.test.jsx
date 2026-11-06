// @vitest-environment jsdom

import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from '../App.jsx'

afterEach(() => {
  cleanup()
  window.history.replaceState({}, '', '/')
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

function crearCatalogo() {
  return {
    version: { nombre: 'SEA-CU 2025' },
    dimensiones: Array.from({ length: 6 }, (_, indice) => {
      const codigo = String(indice + 1)
      const criterio = indice === 2
        ? {
          codigo: '3.2.4',
          texto: 'Investigación de estudiantes',
          tipo_dato: 'cuantitativo',
          solo_en_guia: true,
        }
        : {
          codigo: `${codigo}.1.1`,
          texto: `Criterio de prueba ${codigo}`,
          tipo_dato: 'cualitativo',
          solo_en_guia: false,
        }

      return {
        codigo,
        nombre: `Dimensión ${codigo}`,
        orden: indice + 1,
        indicadores: [{
          codigo: indice === 2 ? '3.2' : `${codigo}.1`,
          texto: `Indicador de prueba ${codigo}`,
          criterios: [criterio],
        }],
      }
    }),
  }
}

function crearFicha() {
  return {
    codigo: '3.2.4',
    codigo_manual: null,
    codigo_guia: '3.2.4',
    solo_en_guia: true,
    texto: 'Investigación de estudiantes',
    tipo_dato: 'cuantitativo',
    valoracion_por_categoria: true,
    nota_normativa: 'Nota normativa de prueba.',
    evidencias: [{
      texto: 'Encuesta a estudiantes',
      orden: 1,
      es_verificacion_externa: true,
    }],
    requisitos_por_categoria: [{
      categoria: 'excelencia',
      texto: 'Requisito de referencia.',
    }],
    modelos: [{
      numero: 1,
      numero_rm36: '1',
      nombre: 'Modelo institucional',
    }],
  }
}

function respuesta(datos, ok = true) {
  return {
    ok,
    text: async () => JSON.stringify(datos),
  }
}

describe('Catálogo normativo', () => {
  it('muestra las seis dimensiones y permite buscar por código y texto', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(respuesta(crearCatalogo())))
    render(<App />)

    expect(await screen.findByText('6 dimensiones · 6 criterios')).toBeTruthy()
    for (let indice = 1; indice <= 6; indice += 1) {
      expect(screen.getByText(new RegExp(`^${indice} Dimensión ${indice}`))).toBeTruthy()
    }

    const busqueda = screen.getByRole('searchbox', {
      name: 'Buscar por código o texto',
    })
    fireEvent.change(busqueda, { target: { value: '3.2.4' } })

    expect(await screen.findByRole('link', {
      name: '3.2.4 — Investigación de estudiantes',
    })).toBeTruthy()
    expect(screen.getByText('Cuantitativo')).toBeTruthy()
    expect(screen.getByText('Solo en la Guía')).toBeTruthy()
    expect(screen.getByText('1 dimensiones · 1 criterios')).toBeTruthy()

    fireEvent.change(busqueda, { target: { value: 'Investigación de estudiantes' } })

    expect(screen.getByRole('link', {
      name: '3.2.4 — Investigación de estudiantes',
    })).toBeTruthy()
  })

  it('navega a la ficha y muestra carga, evidencias, requisitos y modelos', async () => {
    const usuario = userEvent.setup()
    let resolverFicha
    const fichaPendiente = new Promise((resolve) => {
      resolverFicha = resolve
    })
    const fetchMock = vi.fn((url) => (
      String(url).includes('/criterios/')
        ? fichaPendiente
        : Promise.resolve(respuesta(crearCatalogo()))
    ))
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    const busqueda = await screen.findByRole('searchbox', {
      name: 'Buscar por código o texto',
    })
    fireEvent.change(busqueda, { target: { value: '3.2.4' } })
    await usuario.click(await screen.findByRole('link', {
      name: '3.2.4 — Investigación de estudiantes',
    }))

    expect((await screen.findByRole('status')).textContent).toContain(
      'Cargando ficha de criterio...',
    )
    await act(async () => {
      resolverFicha(respuesta(crearFicha()))
    })

    expect(await screen.findByRole('heading', { name: 'Criterio 3.2.4' })).toBeTruthy()
    expect(screen.getByText('Encuesta a estudiantes')).toBeTruthy()
    expect(screen.getByText('Verificación externa')).toBeTruthy()
    expect(screen.getByText(/Los requisitos se presentan como referencia/)).toBeTruthy()
    expect(screen.getAllByRole('alert').some((alerta) => (
      alerta.textContent.includes('el sistema no calcula la categoría de acreditación.')
    ))).toBe(true)
    expect(screen.getByText('Requisito de referencia.')).toBeTruthy()
    expect(screen.getByText('Nota normativa de prueba.')).toBeTruthy()
    expect(screen.getByText(/Modelo 1 \(RM 36: 1\) — Modelo institucional/)).toBeTruthy()
  })

  it('muestra el error de la API cuando no se puede cargar la ficha', async () => {
    const usuario = userEvent.setup()
    const fetchMock = vi.fn((url) => (
      String(url).includes('/criterios/')
        ? Promise.resolve(respuesta({
          codigo: 'no_encontrado',
          mensaje: 'No existe el criterio.',
          detalle: null,
        }, false))
        : Promise.resolve(respuesta(crearCatalogo()))
    ))
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    const busqueda = await screen.findByRole('searchbox', {
      name: 'Buscar por código o texto',
    })
    fireEvent.change(busqueda, { target: { value: '3.2.4' } })
    await usuario.click(await screen.findByRole('link', {
      name: '3.2.4 — Investigación de estudiantes',
    }))

    expect((await screen.findByRole('alert')).textContent).toContain(
      'no_encontrado: No existe el criterio.',
    )
  })
})
