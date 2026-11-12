function normalizarEntero(valor) {
  const numero = Number(valor)
  if (!Number.isFinite(numero)) {
    return null
  }
  return Math.trunc(numero)
}

function normalizarDecimal(valor) {
  if (valor === null || valor === undefined) {
    return null
  }
  const texto = String(valor).trim().replace(',', '.')
  if (!texto) {
    return null
  }
  const numero = Number(texto)
  if (!Number.isFinite(numero)) {
    return null
  }
  return numero
}

export function formatearAsistentePorcentaje(porcentaje, numerador, denominador) {
  const numeradorNormalizado = normalizarEntero(numerador)
  const denominadorNormalizado = normalizarEntero(denominador)

  if (numeradorNormalizado === null || numeradorNormalizado < 0) {
    throw new Error('Debe indicar un numerador entero mayor o igual que cero.')
  }
  if (denominadorNormalizado === null || denominadorNormalizado <= 0) {
    throw new Error('Debe indicar un denominador entero mayor que cero.')
  }

  const porcentajeNormalizado = normalizarDecimal(porcentaje)
  const porcentajeFinal = porcentajeNormalizado === null
    ? ((numeradorNormalizado / denominadorNormalizado) * 100)
    : porcentajeNormalizado
  return `${porcentajeFinal.toFixed(1).replace('.', ',')} % (${numeradorNormalizado}/${denominadorNormalizado})`
}
