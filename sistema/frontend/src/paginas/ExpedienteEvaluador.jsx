import { useEffect, useMemo, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

function extraerLista(respuesta) {
  if (Array.isArray(respuesta)) return respuesta
  if (Array.isArray(respuesta?.results)) return respuesta.results
  return []
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
        evidencias.length === 0 ? <Mensaje tipo="info">El expediente no contiene evidencias.</Mensaje> : (
          <div aria-label="Árbol del expediente" className="d-grid gap-2">
            {evidencias.map((evidencia) => (
              <details className="border rounded p-3" key={evidencia.id}>
                <summary>
                  <strong>{evidencia.titulo}</strong>
                  <span className="badge text-bg-light ms-2">Tipo {evidencia.tipo_evidencia}</span>
                </summary>
                {evidencia.descripcion ? <p className="mt-3 mb-2">{evidencia.descripcion}</p> : null}
                {evidencia.clasificaciones?.length ? (
                  <ul>
                    {evidencia.clasificaciones.map((clasificacion) => (
                      <li key={clasificacion.id}>Criterio {clasificacion.criterio}</li>
                    ))}
                  </ul>
                ) : null}
                {evidencia.ficheros?.length ? (
                  <ul>
                    {evidencia.ficheros.map((fichero) => (
                      <li key={fichero.id}>
                        <a href={`/api/ciclos/${cicloId}/expediente/ficheros/${fichero.id}/descarga/`}>
                          {fichero.nombre_original}
                        </a>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </details>
            ))}
          </div>
        )
      ) : null}
    </section>
  )
}

export default ExpedienteEvaluador
