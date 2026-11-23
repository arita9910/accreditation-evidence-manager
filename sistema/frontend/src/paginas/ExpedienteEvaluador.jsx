import { useEffect, useMemo, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

function extraerLista(respuesta) {
  if (Array.isArray(respuesta)) return respuesta
  if (Array.isArray(respuesta?.results)) return respuesta.results
  return []
}

function normalizarValoraciones(criterio) {
  if (Array.isArray(criterio?.valoraciones) && criterio.valoraciones.length > 0) {
    return criterio.valoraciones
      .filter((valoracion) => valoracion?.texto)
      .map((valoracion) => ({
        tipo: valoracion.tipo,
        texto: valoracion.texto,
      }))
  }
  const fortalezas = (criterio?.fortalezas ?? []).map((texto) => ({ tipo: 'fortaleza', texto }))
  const debilidades = (criterio?.debilidades ?? []).map((texto) => ({ tipo: 'debilidad', texto }))
  return [...fortalezas, ...debilidades]
}

function ExpedienteEvaluador({ usuario }) {
  const autorizado = usuario?.rol === 'par_evaluador'
  const [ciclos, setCiclos] = useState([])
  const [cicloId, setCicloId] = useState('')
  const [expediente, setExpediente] = useState(null)
  const [cargando, setCargando] = useState(autorizado)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!autorizado) {
      setCargando(false)
      return undefined
    }
    let vigente = true
    peticion('/api/ciclos/')
      .then((respuesta) => {
        if (!vigente) return
        const lista = extraerLista(respuesta)
        setCiclos(lista)
        if (lista.length > 0) setCicloId(String(lista[0].id))
      })
      .catch((errorRecibido) => vigente && setError(errorRecibido.message))
      .finally(() => vigente && setCargando(false))
    return () => { vigente = false }
  }, [autorizado])

  useEffect(() => {
    if (!cicloId) return undefined
    let vigente = true
    setError('')
    peticion(`/api/ciclos/${cicloId}/expediente/`)
      .then((respuesta) => vigente && setExpediente(respuesta))
      .catch((errorRecibido) => {
        if (vigente) {
          setExpediente(null)
          setError(errorRecibido.message)
        }
      })
    return () => { vigente = false }
  }, [cicloId])

  const evidencias = useMemo(() => expediente?.evidencias ?? [], [expediente])
  const dimensiones = useMemo(() => expediente?.dimensiones ?? [], [expediente])

  const evidenciasPorCriterio = useMemo(() => {
    const agrupadas = {}
    evidencias.forEach((evidencia) => {
      evidencia.clasificaciones?.forEach((clasificacion) => {
        const criterioId = clasificacion.criterio
        agrupadas[criterioId] = [...(agrupadas[criterioId] ?? []), evidencia]
      })
    })
    return agrupadas
  }, [evidencias])

  if (!autorizado) {
    return <Mensaje tipo="error" titulo="Acceso denegado">Solo el par evaluador puede consultar este expediente.</Mensaje>
  }
  if (cargando) return <Cargando texto="Cargando expediente..." />

  return (
    <section aria-labelledby="titulo-expediente">
      <h1 id="titulo-expediente">Expediente del ciclo</h1>
      <p className="text-body-secondary">Vista de solo lectura. No están disponibles acciones de creación, edición o eliminación.</p>
      {error ? <Mensaje tipo="error" titulo="No se pudo abrir el expediente">{error}</Mensaje> : null}
      <div className="mb-4">
        <label className="form-label" htmlFor="expediente-ciclo">Ciclo asignado</label>
        <select className="form-select" id="expediente-ciclo" value={cicloId} onChange={(evento) => setCicloId(evento.target.value)}>
          <option value="">Seleccione un ciclo</option>
          {ciclos.map((item) => (
            <option key={item.id} value={item.id}>{item.tipo} · {item.anio_base}</option>
          ))}
        </select>
      </div>
      {expediente ? (
        <>
          {dimensiones.length > 0 ? (
            <div aria-label="Árbol del catálogo y expediente" className="d-grid gap-3">
              {dimensiones.map((dimension) => (
                <details className="border rounded p-3" key={dimension.id} open>
                  <summary><strong>{dimension.codigo} · {dimension.nombre}</strong></summary>
                  <div className="mt-3 d-grid gap-3">
                    {dimension.indicadores.map((indicador) => (
                      <section key={indicador.id}>
                        <h2 className="h6">{indicador.codigo} · {indicador.texto}</h2>
                        <div className="d-grid gap-2">
                          {indicador.criterios.map((criterio) => {
                            const valoraciones = normalizarValoraciones(criterio)
                            return (
                              <article className="border-start border-3 ps-3" key={criterio.id}>
                                <strong>{criterio.codigo}</strong> — {criterio.texto}
                                {valoraciones.length ? (
                                  <div className="mt-2 d-grid gap-2">
                                    {valoraciones.map((valoracion, indice) => (
                                      <div
                                        className={`rounded px-2 py-1 ${
                                          valoracion.tipo === 'fortaleza'
                                            ? 'bg-success-subtle border border-success-subtle'
                                            : 'bg-warning-subtle border border-warning-subtle'
                                        }`}
                                        key={`${valoracion.tipo}-${indice}`}
                                      >
                                        <strong>{valoracion.tipo === 'fortaleza' ? 'Fortaleza' : 'Debilidad'}:</strong> {valoracion.texto}
                                      </div>
                                    ))}
                                  </div>
                                ) : null}
                                {evidenciasPorCriterio[criterio.id]?.length ? (
                                  <div className="mt-2">
                                    <strong>Evidencias</strong>
                                    <ul>
                                      {evidenciasPorCriterio[criterio.id].map((evidencia) => (
                                        <li key={evidencia.id}>
                                          {evidencia.titulo}
                                          {evidencia.ficheros?.map((fichero) => (
                                            <a
                                              className="ms-2"
                                              key={fichero.id}
                                              href={`/api/ciclos/${cicloId}/expediente/ficheros/${fichero.id}/descarga/`}
                                            >
                                              {fichero.nombre_original}
                                            </a>
                                          ))}
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                ) : null}
                              </article>
                            )
                          })}
                        </div>
                      </section>
                    ))}
                  </div>
                </details>
              ))}
            </div>
          ) : evidencias.length === 0 ? (
            <Mensaje tipo="info">El expediente no contiene evidencias ni valoraciones.</Mensaje>
          ) : null}
        </>
      ) : null}
    </section>
  )
}

export default ExpedienteEvaluador
