// @vitest-environment jsdom

import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App.jsx'

describe('App', () => {
  it('renders the starter page and increments its counter', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'Get started' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Count is 0' }))
    expect(screen.getByRole('button', { name: 'Count is 1' })).toBeTruthy()
  }, 30000)
})
