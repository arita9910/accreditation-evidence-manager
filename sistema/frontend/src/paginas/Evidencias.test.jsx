// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Evidencias from './Evidencias.jsx'

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

describe('Pantalla de evidencias', () => {
  it('carga listado, aplica filtros y marca visualmente evidencias en papel', async () => {
    const fetchMock = vi.fn((url, opciones = {}) => {
      const ruta = rutaApi(url)
      const [pathname, queryString = ''] = ruta.split('?')
      const query = new URLSearchParams(queryString)

      if (pathname === '/api/evidencias/' && !opciones.method) {
        if (query.get('q') === 'acta' && query.get('soporte') === 'papel') {
          return Promise.resolve(respuesta({
            results: [{
              id: 2,
              ciclo: 11,
              titulo: 'Acta física',
              curso_academico: 2025,
              soporte: 'papel',
              estado_huella: null,
            }],
          }))
        }
        return Promise.resolve(respuesta({
          results: [{
            id: 1,
            ciclo: 10,
            titulo: 'Informe final',
            curso_academico: 2025,
            soporte: 'digital',
            estado_huella: 'correcta',
          }],
        }))
      }

      if (pathname === '/api/ciclos/' && !opciones.method) {
        return Promise.resolve(respuesta({
          results: [{ id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 2 }],
        }))
      }

      if (pathname === '/api/evidencias/2/' && !opciones.method) {
        return Promise.resolve(respuesta({
          id: 2,
          titulo: 'Acta física',
          soporte: 'papel',
          estado_huella: null,
          periodo_desde: '2025-01-01',
          periodo_hasta: '2025-12-31',
          ficheros: [],
        }))
      }

      return Promise.resolve(respuesta({ codigo: 'not_found', mensaje: 'No encontrado.' }, false))
    })
    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter>
        <Evidencias usuario={{ id: 1, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Gestión de evidencias' })).toBeTruthy()
    expect(await screen.findByText('Informe final')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Búsqueda'), { target: { value: 'acta' } })
    fireEvent.change(screen.getByLabelText('Soporte', { selector: '#evidencias-soporte' }), { target: { value: 'papel' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    expect(await screen.findByText('Acta física')).toBeTruthy()
    expect(screen.getByText('Papel', { selector: 'span.badge' })).toBeTruthy()

    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/api/evidencias/?q=acta&soporte=papel'))).toBe(true)
  }, 15000)

  it('envía el formulario de carga y muestra detalle con historial de versiones', async () => {
    const fetchMock = vi.fn((url, opciones = {}) => {
      const ruta = rutaApi(url)
      const metodo = (opciones.method || 'GET').toUpperCase()

      if (ruta === '/api/evidencias/' && metodo === 'GET') {
        return Promise.resolve(respuesta({ results: [] }))
      }
      if (ruta === '/api/ciclos/' && metodo === 'GET') {
        return Promise.resolve(respuesta({
          results: [{ id: 10, tipo: 'ordinario', anio_base: 2026, carrera: 2 }],
        }))
      }
      if (ruta === '/api/evidencias/' && metodo === 'POST') {
        return Promise.resolve(respuesta({ id: 9, titulo: 'Informe anual' }, true))
      }
      if (ruta === '/api/evidencias/9/' && metodo === 'GET') {
        return Promise.resolve(respuesta({
          id: 9,
          titulo: 'Informe anual',
          soporte: 'digital',
          estado_huella: 'correcta',
          periodo_desde: '2025-01-01',
          periodo_hasta: '2025-12-31',
          ficheros: [
            { id: 21, version: 1, nombre_original: 'informe-v1.pdf', sha256: 'a'.repeat(64), vigente: false },
            { id: 22, version: 2, nombre_original: 'informe-v2.pdf', sha256: 'b'.repeat(64), vigente: true },
          ],
        }))
      }

      return Promise.resolve(respuesta({ codigo: 'not_found', mensaje: 'No encontrado.' }, false))
    })
    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter>
        <Evidencias usuario={{ id: 1, rol: 'director_carrera' }} />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Formulario de carga' })).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Ciclo', { selector: '#evidencia-ciclo' }), { target: { value: '10' } })
    fireEvent.change(screen.getByLabelText('Tipo de evidencia (ID)'), { target: { value: '6' } })
    fireEvent.change(screen.getByLabelText('Título'), { target: { value: 'Informe anual' } })
    fireEvent.change(screen.getByLabelText('Curso académico'), { target: { value: '2025' } })
    fireEvent.change(screen.getByLabelText('Periodo desde'), { target: { value: '2025-01-01' } })
    fireEvent.change(screen.getByLabelText('Periodo hasta'), { target: { value: '2025-12-31' } })
    fireEvent.change(screen.getByLabelText('Descripción'), { target: { value: 'Versión inicial' } })

    const archivo = new File(['contenido'], 'informe.pdf', { type: 'application/pdf' })
    fireEvent.change(screen.getByLabelText('Archivo'), { target: { files: [archivo] } })

    fireEvent.click(screen.getByRole('button', { name: 'Registrar evidencia' }))

    expect(await screen.findByText('Evidencia creada correctamente.')).toBeTruthy()
    expect(await screen.findByText('Informe anual')).toBeTruthy()
    expect(screen.getByText('informe-v2.pdf')).toBeTruthy()
    expect(screen.getByText(/Estado de huella:/)).toBeTruthy()

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(([, opciones = {}]) => (opciones.method || '').toUpperCase() === 'POST')
      expect(llamada).toBeTruthy()
      const [, opciones] = llamada
      expect(opciones.body.get('titulo')).toBe('Informe anual')
      expect(opciones.body.get('soporte')).toBe('digital')
      expect(opciones.body.get('archivo')).toBeTruthy()
    }, 15000)
  })
})
