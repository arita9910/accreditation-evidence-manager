import { useCallback, useEffect, useMemo, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

function extraerLista(respuesta) {
  if (Array.isArray(respuesta)) {
    return respuesta
  }
  if (Array.isArray(respuesta?.results)) {
    return respuesta.results
  }
  return []
}

function parsearNumeroTexto(valor) {
  const texto = String(valor ?? '').trim()
  if (!texto) {
    return null
  }
  const numero = Number(texto.replace(',', '.'))
  if (!Number.isFinite(numero)) {
    return null
  }
  return numero
}

function serializarNumero(valor) {
  const numero = parsearNumeroTexto(valor)
  if (numero === null) {
    return ''
  }
  return String(numero)
}

function validarNoNegativo(valor, etiqueta) {
  if (String(valor ?? '').trim() === '') {
    return ''
  }
  const numero = parsearNumeroTexto(valor)
  if (numero === null) {
    return `El campo ${etiqueta} debe ser numérico.`
  }
  if (numero < 0) {
    return `El campo ${etiqueta} no puede ser negativo.`
  }
  return ''
}

function calcularPorcentaje(numerador, denominador) {
  const numeradorNumero = parsearNumeroTexto(numerador)
  const denominadorNumero = parsearNumeroTexto(denominador)
  if (numeradorNumero === null || denominadorNumero === null || denominadorNumero <= 0) {
    return ''
  }
  return ((numeradorNumero / denominadorNumero) * 100).toFixed(1)
}

function formatearDato(dato) {
  const etiquetaTipo = dato.tipo === 'modelo' ? `Modelo ${dato.modelo}` : `Criterio ${dato.codigo ?? dato.criterio}`
  const valor = dato.valor ?? '—'
  return `${etiquetaTipo} · valor ${valor}`
}

function Cuantitativos({ usuario }) {
  const [ciclos, setCiclos] = useState([])
  const [modelos, setModelos] = useState([])
  const [catalogo, setCatalogo] = useState(null)
  const [cicloId, setCicloId] = useState('')
  const [modeloNumero, setModeloNumero] = useState('')
  const [curso, setCurso] = useState('')
  const [criterioCodigo, setCriterioCodigo] = useState('')
  const [celdas, setCeldas] = useState([])
  const [valorCriterio, setValorCriterio] = useState({
    valor: '',
    numerador: '',
    denominador: '',
    curso: '',
    unidad: '',
    observacion: '',
  })
  const [sinRespaldo, setSinRespaldo] = useState([])
  const [evidenciasDato, setEvidenciasDato] = useState([])
  const [datoSeleccionado, setDatoSeleccionado] = useState('')
  const [evidenciaId, setEvidenciaId] = useState('')
  const [cargando, setCargando] = useState(true)
  const [guardandoModelo, setGuardandoModelo] = useState(false)
  const [guardandoCriterio, setGuardandoCriterio] = useState(false)
  const [vinculando, setVinculando] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')
  const [errorModelo, setErrorModelo] = useState('')
  const [errorCriterio, setErrorCriterio] = useState('')
  const [errorVinculo, setErrorVinculo] = useState('')

  const puedeEditar = usuario?.rol === 'administrador_tecnico' || usuario?.rol === 'director_carrera'

  useEffect(() => {
    let vigente = true
    const cargar = async () => {
      setCargando(true)
      setError('')
      try {
        const [respuestaCiclos, respuestaModelos, respuestaCatalogo] = await Promise.all([
          peticion('/api/ciclos/'),
          peticion('/api/catalogo/modelos/'),
          peticion('/api/catalogo/'),
        ])
        if (!vigente) {
          return
        }
        const ciclosRecibidos = extraerLista(respuestaCiclos)
        const modelosRecibidos = extraerLista(respuestaModelos)
        setCiclos(ciclosRecibidos)
        setModelos(modelosRecibidos)
        setCatalogo(respuestaCatalogo)
        if (ciclosRecibidos.length > 0) {
          const cicloBase = ciclosRecibidos[0]
          setCicloId(String(cicloBase.id))
          setCurso(String(cicloBase.curso_final ?? ''))
          setValorCriterio((previo) => ({ ...previo, curso: String(cicloBase.curso_final ?? '') }))
        }
        if (modelosRecibidos.length > 0) {
          setModeloNumero(String(modelosRecibidos[0].numero))
        }
      } catch (errorRecibido) {
        if (vigente) {
          setError(errorRecibido.message)
        }
      } finally {
        if (vigente) {
          setCargando(false)
        }
      }
    }
    cargar()
    return () => {
      vigente = false
    }
  }, [])

  const criteriosSinModelo = useMemo(() => extraerLista(catalogo?.dimensiones)
    .flatMap((dimension) => extraerLista(dimension?.indicadores))
    .flatMap((indicador) => extraerLista(indicador?.criterios))
    .filter((criterio) => criterio?.tipo_dato === 'cuantitativo' && extraerLista(criterio?.modelos).length === 0), [catalogo])

  useEffect(() => {
    if (!criterioCodigo && criteriosSinModelo.length > 0) {
      setCriterioCodigo(criteriosSinModelo[0].codigo)
    }
  }, [criterioCodigo, criteriosSinModelo])

  const modeloSeleccionado = useMemo(
    () => modelos.find((modelo) => String(modelo.numero) === String(modeloNumero)) ?? null,
    [modelos, modeloNumero],
  )

  const criterioSeleccionado = useMemo(
    () => criteriosSinModelo.find((criterio) => criterio.codigo === criterioCodigo) ?? null,
    [criteriosSinModelo, criterioCodigo],
  )

  const cargarSinRespaldo = useCallback(async (cicloActual) => {
    if (!cicloActual) {
      setSinRespaldo([])
      return
    }
    const respuesta = await peticion(`/api/ciclos/${cicloActual}/datos/sin-respaldo/`)
    setSinRespaldo(extraerLista(respuesta?.datos_sin_respaldo ?? respuesta?.datos))
  }, [])

  const cargarModelo = useCallback(async () => {
    if (!cicloId || !modeloNumero || !curso) {
      setCeldas([])
      return
    }
    setErrorModelo('')
    const respuesta = await peticion(`/api/ciclos/${cicloId}/modelos/${modeloNumero}/valores/?curso=${curso}`)
    const celdasRecibidas = extraerLista(respuesta?.celdas)
    const mapaPorCampo = new Map(celdasRecibidas.map((celda) => [String(celda.campo), celda]))
    const camposModelo = extraerLista(modeloSeleccionado?.campos)
    const siguienteCeldas = camposModelo.map((campo) => {
      const valorDeLaApi = mapaPorCampo.get(String(campo.id))
      return {
        campo: campo.id,
        fila: campo.fila,
        columna: campo.columna,
        tipo_valor: campo.tipo_valor,
        etiqueta_fila: valorDeLaApi?.etiqueta_fila,
        etiqueta_columna: valorDeLaApi?.etiqueta_columna,
        valor: serializarNumero(valorDeLaApi?.valor),
        numerador: serializarNumero(valorDeLaApi?.numerador),
        denominador: serializarNumero(valorDeLaApi?.denominador),
      }
    })
    setCeldas(siguienteCeldas)
  }, [cicloId, modeloNumero, curso, modeloSeleccionado])

  const cargarValorCriterio = useCallback(async () => {
    if (!cicloId || !criterioCodigo) {
      return
    }
    setErrorCriterio('')
    const respuesta = await peticion(`/api/ciclos/${cicloId}/criterios/${criterioCodigo}/valor/`)
    const valor = respuesta?.valor ?? {}
    setValorCriterio((previo) => ({
      ...previo,
      valor: serializarNumero(valor.valor),
      numerador: serializarNumero(valor.numerador),
      denominador: serializarNumero(valor.denominador),
      curso: serializarNumero(valor.curso) || previo.curso,
      unidad: String(valor.unidad ?? ''),
      observacion: String(valor.observacion ?? ''),
    }))
  }, [cicloId, criterioCodigo])

  useEffect(() => {
    if (!cargando && cicloId) {
      cargarSinRespaldo(cicloId).catch((errorRecibido) => setErrorVinculo(errorRecibido.message))
    }
  }, [cargando, cicloId, cargarSinRespaldo])

  useEffect(() => {
    if (!cargando && modeloSeleccionado) {
      cargarModelo().catch((errorRecibido) => setErrorModelo(errorRecibido.message))
    }
  }, [cargando, modeloSeleccionado, cargarModelo])

  useEffect(() => {
    if (!cargando && criterioCodigo) {
      cargarValorCriterio().catch((errorRecibido) => setErrorCriterio(errorRecibido.message))
    }
  }, [cargando, criterioCodigo, cargarValorCriterio])

  useEffect(() => {
    if (!datoSeleccionado) {
      setEvidenciasDato([])
      return
    }
    const [tipo, id] = datoSeleccionado.split(':')
    peticion(`/api/datos/${tipo}/${id}/evidencias/`)
      .then((respuesta) => setEvidenciasDato(extraerLista(respuesta?.evidencias)))
      .catch((errorRecibido) => setErrorVinculo(errorRecibido.message))
  }, [datoSeleccionado])

  const totalValor = useMemo(
    () => celdas.reduce((acumulado, celda) => acumulado + (parsearNumeroTexto(celda.valor) ?? 0), 0),
    [celdas],
  )
  const totalNumerador = useMemo(
    () => celdas.reduce((acumulado, celda) => acumulado + (parsearNumeroTexto(celda.numerador) ?? 0), 0),
    [celdas],
  )
  const totalDenominador = useMemo(
    () => celdas.reduce((acumulado, celda) => acumulado + (parsearNumeroTexto(celda.denominador) ?? 0), 0),
    [celdas],
  )

  const actualizarCelda = (indice, campo, valor) => {
    setCeldas((previo) => previo.map((celda, actual) => (
      indice === actual
        ? { ...celda, [campo]: valor }
        : celda
    )))
    setErrorModelo('')
  }

  const guardarModelo = async (evento) => {
    evento.preventDefault()
    setMensaje('')
    setErrorModelo('')
    for (const celda of celdas) {
      const errorValor = validarNoNegativo(celda.valor, `(${celda.fila},${celda.columna})`)
      const errorNumerador = validarNoNegativo(celda.numerador, `numerador (${celda.fila},${celda.columna})`)
      const errorDenominador = validarNoNegativo(celda.denominador, `denominador (${celda.fila},${celda.columna})`)
      if (errorValor || errorNumerador || errorDenominador) {
        setErrorModelo(errorValor || errorNumerador || errorDenominador)
        return
      }
    }

    setGuardandoModelo(true)
    try {
      await peticion(`/api/ciclos/${cicloId}/modelos/${modeloNumero}/valores/?curso=${curso}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          curso,
          celdas: celdas.map((celda) => ({
            campo: celda.campo,
            valor: celda.valor === '' ? null : parsearNumeroTexto(celda.valor),
            numerador: celda.numerador === '' ? null : parsearNumeroTexto(celda.numerador),
            denominador: celda.denominador === '' ? null : parsearNumeroTexto(celda.denominador),
          })),
        }),
      })
      setMensaje('Valores de modelo guardados.')
      await cargarSinRespaldo(cicloId)
    } catch (errorRecibido) {
      setErrorModelo(errorRecibido.message)
    } finally {
      setGuardandoModelo(false)
    }
  }

  const guardarCriterio = async (evento) => {
    evento.preventDefault()
    setMensaje('')
    setErrorCriterio('')
    const errorValor = validarNoNegativo(valorCriterio.valor, 'valor del criterio')
    const errorNumerador = validarNoNegativo(valorCriterio.numerador, 'numerador del criterio')
    const errorDenominador = validarNoNegativo(valorCriterio.denominador, 'denominador del criterio')
    if (errorValor || errorNumerador || errorDenominador) {
      setErrorCriterio(errorValor || errorNumerador || errorDenominador)
      return
    }

    setGuardandoCriterio(true)
    try {
      await peticion(`/api/ciclos/${cicloId}/criterios/${criterioCodigo}/valor/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          curso: valorCriterio.curso || null,
          valor: valorCriterio.valor === '' ? null : parsearNumeroTexto(valorCriterio.valor),
          numerador: valorCriterio.numerador === '' ? null : parsearNumeroTexto(valorCriterio.numerador),
          denominador: valorCriterio.denominador === '' ? null : parsearNumeroTexto(valorCriterio.denominador),
          unidad: valorCriterio.unidad,
          observacion: valorCriterio.observacion,
        }),
      })
      setMensaje('Valor de criterio guardado.')
      await cargarSinRespaldo(cicloId)
    } catch (errorRecibido) {
      setErrorCriterio(errorRecibido.message)
    } finally {
      setGuardandoCriterio(false)
    }
  }

  const vincularDato = async (evento) => {
    evento.preventDefault()
    setMensaje('')
    setErrorVinculo('')
    if (!datoSeleccionado || !evidenciaId) {
      setErrorVinculo('Seleccione un dato y una evidencia.')
      return
    }
    const [tipo, id] = datoSeleccionado.split(':')
    setVinculando(true)
    try {
      await peticion('/api/vinculos/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dato: { tipo, id }, evidencia: evidenciaId }),
      })
      setMensaje('Dato vinculado con evidencia.')
      await Promise.all([
        cargarSinRespaldo(cicloId),
        peticion(`/api/datos/${tipo}/${id}/evidencias/`).then((respuesta) => setEvidenciasDato(extraerLista(respuesta?.evidencias))),
      ])
    } catch (errorRecibido) {
      setErrorVinculo(errorRecibido.message)
    } finally {
      setVinculando(false)
    }
  }

  if (cargando) {
    return <Cargando texto="Cargando pantalla de cuantitativos..." />
  }

  if (error) {
    return <Mensaje tipo="error" titulo="No se pudo cargar cuantitativos">{error}</Mensaje>
  }

  return (
    <section aria-labelledby="titulo-cuantitativos" className="d-grid gap-4">
      <header>
        <h1 id="titulo-cuantitativos">Datos cuantitativos</h1>
        <p className="text-body-secondary mb-0">
          El sistema no evalúa el cumplimiento; los datos de la Guía se muestran solo como referencia.
        </p>
      </header>

      {mensaje ? <Mensaje tipo="success">{mensaje}</Mensaje> : null}

      <section className="card">
        <div className="card-body">
          <h2 className="h5">Contexto de captura</h2>
          <div className="row g-3">
            <div className="col-md-4">
              <label className="form-label" htmlFor="cuantitativos-ciclo">Ciclo</label>
              <select className="form-select" id="cuantitativos-ciclo" onChange={(evento) => setCicloId(evento.target.value)} value={cicloId}>
                <option value="">Seleccione</option>
                {ciclos.map((ciclo) => (
                  <option key={ciclo.id} value={String(ciclo.id)}>
                    #{ciclo.id} {ciclo.tipo} {ciclo.anio_base}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label" htmlFor="cuantitativos-modelo">Modelo</label>
              <select className="form-select" id="cuantitativos-modelo" onChange={(evento) => setModeloNumero(evento.target.value)} value={modeloNumero}>
                <option value="">Seleccione</option>
                {modelos.map((modelo) => (
                  <option key={modelo.numero} value={String(modelo.numero)}>
                    Modelo {modelo.numero} {modelo.nombre ? `— ${modelo.nombre}` : ''}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label" htmlFor="cuantitativos-curso">Curso</label>
              <input className="form-control" id="cuantitativos-curso" onChange={(evento) => setCurso(evento.target.value)} value={curso} />
            </div>
          </div>
        </div>
      </section>

      <section className="card">
        <div className="card-body">
          <h2 className="h5">Tabla editable por modelo</h2>
          {errorModelo ? <Mensaje tipo="error">{errorModelo}</Mensaje> : null}
          <form onSubmit={guardarModelo}>
            <div className="table-responsive">
              <table className="table table-sm align-middle">
                <thead>
                  <tr>
                    <th scope="col">Celda</th>
                    <th scope="col">Tipo</th>
                    <th scope="col">Valor</th>
                    <th scope="col">Numerador</th>
                    <th scope="col">Denominador</th>
                    <th scope="col">% calculado</th>
                  </tr>
                </thead>
                <tbody>
                  {celdas.map((celda, indice) => (
                    <tr key={celda.campo}>
                      <td>{celda.etiqueta_fila || celda.fila},{celda.etiqueta_columna || celda.columna}</td>
                      <td>{celda.tipo_valor}</td>
                      <td>
                        <input
                          aria-label={`valor-${celda.fila}-${celda.columna}`}
                          className="form-control form-control-sm"
                          inputMode="decimal"
                          onChange={(evento) => actualizarCelda(indice, 'valor', evento.target.value)}
                          value={celda.valor}
                        />
                      </td>
                      <td>
                        <input
                          aria-label={`numerador-${celda.fila}-${celda.columna}`}
                          className="form-control form-control-sm"
                          inputMode="decimal"
                          onChange={(evento) => actualizarCelda(indice, 'numerador', evento.target.value)}
                          value={celda.numerador}
                        />
                      </td>
                      <td>
                        <input
                          aria-label={`denominador-${celda.fila}-${celda.columna}`}
                          className="form-control form-control-sm"
                          inputMode="decimal"
                          onChange={(evento) => actualizarCelda(indice, 'denominador', evento.target.value)}
                          value={celda.denominador}
                        />
                      </td>
                      <td>{calcularPorcentaje(celda.numerador, celda.denominador) || '—'}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <th scope="row">Totales</th>
                    <td />
                    <td>{totalValor.toFixed(1)}</td>
                    <td>{totalNumerador.toFixed(1)}</td>
                    <td>{totalDenominador.toFixed(1)}</td>
                    <td>{totalDenominador > 0 ? ((totalNumerador / totalDenominador) * 100).toFixed(1) : '—'}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
            {puedeEditar ? (
              <button className="btn btn-primary" disabled={guardandoModelo} type="submit">
                {guardandoModelo ? 'Guardando...' : 'Guardar modelo'}
              </button>
            ) : (
              <Mensaje tipo="warning">Tu rol no permite editar datos cuantitativos.</Mensaje>
            )}
          </form>
        </div>
      </section>

      <section className="card">
        <div className="card-body">
          <h2 className="h5">Valor por criterio sin modelo</h2>
          {errorCriterio ? <Mensaje tipo="error">{errorCriterio}</Mensaje> : null}
          <form className="row g-3" onSubmit={guardarCriterio}>
            <div className="col-md-4">
              <label className="form-label" htmlFor="criterio-cuantitativo">Criterio</label>
              <select className="form-select" id="criterio-cuantitativo" onChange={(evento) => setCriterioCodigo(evento.target.value)} value={criterioCodigo}>
                <option value="">Seleccione</option>
                {criteriosSinModelo.map((criterio) => (
                  <option key={criterio.codigo} value={criterio.codigo}>
                    {criterio.codigo} {criterio.texto}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="criterio-valor">Valor</label>
              <input className="form-control" id="criterio-valor" inputMode="decimal" onChange={(evento) => setValorCriterio((previo) => ({ ...previo, valor: evento.target.value }))} value={valorCriterio.valor} />
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="criterio-numerador">Numerador</label>
              <input className="form-control" id="criterio-numerador" inputMode="decimal" onChange={(evento) => setValorCriterio((previo) => ({ ...previo, numerador: evento.target.value }))} value={valorCriterio.numerador} />
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="criterio-denominador">Denominador</label>
              <input className="form-control" id="criterio-denominador" inputMode="decimal" onChange={(evento) => setValorCriterio((previo) => ({ ...previo, denominador: evento.target.value }))} value={valorCriterio.denominador} />
            </div>
            <div className="col-md-2">
              <label className="form-label" htmlFor="criterio-curso">Curso</label>
              <input className="form-control" id="criterio-curso" inputMode="numeric" onChange={(evento) => setValorCriterio((previo) => ({ ...previo, curso: evento.target.value }))} value={valorCriterio.curso} />
            </div>
            <div className="col-md-3">
              <label className="form-label" htmlFor="criterio-unidad">Unidad</label>
              <input className="form-control" id="criterio-unidad" onChange={(evento) => setValorCriterio((previo) => ({ ...previo, unidad: evento.target.value }))} value={valorCriterio.unidad} />
            </div>
            <div className="col-md-9">
              <label className="form-label" htmlFor="criterio-observacion">Observación</label>
              <input className="form-control" id="criterio-observacion" onChange={(evento) => setValorCriterio((previo) => ({ ...previo, observacion: evento.target.value }))} value={valorCriterio.observacion} />
            </div>
            <div className="col-12">
              <Mensaje tipo="info">
                Referencia de la Guía: {criterioSeleccionado?.requisitos_por_categoria?.length
                  ? criterioSeleccionado.requisitos_por_categoria.map((item) => item.texto).join(' | ')
                  : criterioSeleccionado?.nota_normativa || 'Sin texto de referencia.'}
              </Mensaje>
            </div>
            <div className="col-12">
              {puedeEditar ? (
                <button className="btn btn-primary" disabled={guardandoCriterio} type="submit">
                  {guardandoCriterio ? 'Guardando...' : 'Guardar criterio'}
                </button>
              ) : null}
            </div>
          </form>
        </div>
      </section>

      <section className="card">
        <div className="card-body">
          <h2 className="h5">Vinculación con evidencias y pendientes</h2>
          {errorVinculo ? <Mensaje tipo="error">{errorVinculo}</Mensaje> : null}
          <form className="row g-3" onSubmit={vincularDato}>
            <div className="col-md-5">
              <label className="form-label" htmlFor="dato-sin-respaldo">Dato sin respaldo</label>
              <select className="form-select" id="dato-sin-respaldo" onChange={(evento) => setDatoSeleccionado(evento.target.value)} value={datoSeleccionado}>
                <option value="">Seleccione</option>
                {sinRespaldo.map((dato) => (
                  <option key={`${dato.tipo}-${dato.id}`} value={`${dato.tipo}:${dato.id}`}>
                    {formatearDato(dato)}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label" htmlFor="dato-evidencia">Evidencia</label>
              <input className="form-control" id="dato-evidencia" onChange={(evento) => setEvidenciaId(evento.target.value)} placeholder="ID de evidencia" value={evidenciaId} />
            </div>
            <div className="col-md-3 d-flex align-items-end">
              <button className="btn btn-outline-primary w-100" disabled={vinculando} type="submit">
                {vinculando ? 'Vinculando...' : 'Vincular'}
              </button>
            </div>
          </form>

          <div className="mt-3">
            <h3 className="h6">Datos sin respaldo</h3>
            {sinRespaldo.length === 0 ? <Mensaje tipo="info">No hay datos sin respaldo.</Mensaje> : (
              <ul className="mb-0">
                {sinRespaldo.map((dato) => (
                  <li key={`${dato.tipo}-${dato.id}`}>{formatearDato(dato)}</li>
                ))}
              </ul>
            )}
          </div>

          <div className="mt-3">
            <h3 className="h6">Evidencias del dato seleccionado</h3>
            {evidenciasDato.length === 0 ? <Mensaje tipo="info">Este dato aún no tiene evidencias vinculadas.</Mensaje> : (
              <ul className="mb-0">
                {evidenciasDato.map((evidencia) => (
                  <li key={evidencia.id}>{evidencia.titulo}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>
    </section>
  )
}

export default Cuantitativos
