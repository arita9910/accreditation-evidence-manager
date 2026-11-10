// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Auditoria from './Auditoria.jsx'

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

describe('Pantalla de auditoría', () => {
  it('envía filtros esperados y renderiza paginación con carga de datos', async () => {
    const fetchMock = vi.fn((url) => {
      const texto = String(url)
      const query = texto.split('?')[1] ?? ''
      const params = new URLSearchParams(query)
      const page = params.get('page') ?? '1'

      if (page === '2') {
        return Promise.resolve(respuesta({
          count: 21,
          next: null,
          previous: 'http://testserver/api/auditoria/?page=1',
          results: [{
            id: 2,
            fecha_hora: '2026-01-11T09:30:00',
            usuario: 'director',
            accion: 'ciclo.cerrar',
            entidad: 'Ciclo',
            detalle: { carrera_id: 12 },
            resultado: 'denegado',
          }],
        }))
      }

      return Promise.resolve(respuesta({
        count: 21,
        next: 'http://testserver/api/auditoria/?page=2',
        previous: null,
        results: [{
          id: 1,
          fecha_hora: '2026-01-10T08:00:00',
          usuario: 'auditor',
          accion: 'ciclo.abrir',
          entidad: 'Ciclo',
          detalle: { carrera_id: 12 },
          resultado: 'correcto',
        }],
      }))
    })
    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter>
        <Auditoria />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Consulta de auditoría' })).toBeTruthy()
    expect(await screen.findByText('ciclo.abrir')).toBeTruthy()
    expect(screen.getByText('21 registros · Página 1 de 2')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: 'auditor' } })
    fireEvent.change(screen.getByLabelText('Acción'), { target: { value: 'ciclo' } })
    fireEvent.change(screen.getByLabelText('Desde'), { target: { value: '2026-01-01' } })
    fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2026-01-31' } })
    fireEvent.change(screen.getByLabelText('Resultado'), { target: { value: 'correcto' } })
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }))

    await waitFor(() => {
      const llamada = fetchMock.mock.calls.find(([url]) => {
        const params = new URLSearchParams(String(url).split('?')[1] ?? '')
        return (
          params.get('usuario') === 'auditor'
          && params.get('accion') === 'ciclo'
          && params.get('resultado') === 'correcto'
          && params.get('desde') === '2026-01-01T00:00:00'
          && params.get('hasta') === '2026-01-31T23:59:59'
          && params.get('page') === '1'
        )
      })
      expect(llamada).toBeTruthy()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }))

    expect(await screen.findByText('ciclo.cerrar')).toBeTruthy()
    expect(screen.getByText('21 registros · Página 2 de 2')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeTruthy()
  })
})
