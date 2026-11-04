// @vitest-environment jsdom

import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Mensaje } from './componentes'
import App from './App.jsx'

describe('App', () => {
  it('renderiza la plantilla base del sistema', () => {
    render(<App />)
    expect(screen.getByText('Sistema en preparación.')).toBeTruthy()
  }, 30000)
})

describe('Mensaje', () => {
  it('muestra mensajes de error con el estilo adecuado', () => {
    render(<Mensaje tipo="error" titulo="Error">No se pudo guardar</Mensaje>)

    const alert = screen.getAllByRole('alert').at(-1)
    expect(alert).toHaveTextContent('Error')
    expect(alert).toHaveTextContent('No se pudo guardar')
  })
})
