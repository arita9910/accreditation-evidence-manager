import { useEffect, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

function extraerLista(respuesta) {
  if (Array.isArray(respuesta)) return respuesta
  if (Array.isArray(respuesta?.results)) return respuesta.results
  return []
}

function InformeTextos({ usuario }) {
  const autorizado = usuario?.rol === 'administrador_tecnico' || usuario?.rol === 'director_carrera'
  const [ciclos, setCiclos] = useState([])
  const [cicloId, setCicloId] = useState('')
  const [secciones, setSecciones] = useState([])
  const [contenidos, setContenidos] = useState({})
  const [cargando, setCargando] = useState(autorizado)
  const [guardando, setGuardando] = useState('')
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')

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
        const permitidos = usuario?.rol === 'director_carrera'
          ? lista.filter((ciclo) => String(ciclo.carrera) === String(usuario.carrera))
          : lista
        setCiclos(permitidos)
        if (permitidos.length > 0) setCicloId(String(permitidos[0].id))
      })
      .catch((errorRecibido) => vigente && setError(errorRecibido.message))
      .finally(() => vigente && setCargando(false))
    return () => { vigente = false }
  }, [autorizado, usuario])

  useEffect(() => {
    if (!cicloId) return undefined
    let vigente = true
    setError('')
    setMensaje('')
    peticion(`/api/ciclos/${cicloId}/informe/textos/`)
      .then((respuesta) => {
        if (!vigente) return
        const lista = respuesta.secciones ?? []
        setSecciones(lista)
        setContenidos(Object.fromEntries(lista.map((item) => [item.seccion, item.contenido ?? ''])))
      })
      .catch((errorRecibido) => vigente && setError(errorRecibido.message))
    return () => { vigente = false }
  }, [cicloId])

  const guardar = async (seccion) => {
    setGuardando(seccion)
    setError('')
    setMensaje('')
    try {
      await peticion(`/api/ciclos/${cicloId}/informe/textos/${encodeURIComponent(seccion)}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contenido: contenidos[seccion] ?? '' }),
      })
      setMensaje('Texto guardado correctamente.')
    } catch (errorRecibido) {
      setError(errorRecibido.message)
    } finally {
      setGuardando('')
    }
  }

  if (!autorizado) {
    return <Mensaje tipo="error" titulo="Acceso denegado">Tu rol no permite editar textos del informe.</Mensaje>
  }
  if (cargando) return <Cargando texto="Cargando editor del informe..." />

  const ciclo = ciclos.find((item) => String(item.id) === String(cicloId))
  const cerrado = ciclo?.estado === 'cerrado'

  return (
    <section aria-labelledby="titulo-informe-textos">
      <h1 id="titulo-informe-textos">Textos cualitativos del informe</h1>
      {error ? <Mensaje tipo="error" titulo="Error">{error}</Mensaje> : null}
      {mensaje ? <Mensaje tipo="success" titulo="Guardado">{mensaje}</Mensaje> : null}
      {cerrado ? <Mensaje tipo="warning" titulo="Ciclo cerrado">El ciclo está cerrado. Los textos cualitativos no se pueden modificar.</Mensaje> : null}
      <div className="mb-4">
        <label className="form-label" htmlFor="informe-ciclo">Ciclo</label>
        <select className="form-select" id="informe-ciclo" value={cicloId} onChange={(evento) => setCicloId(evento.target.value)}>
          <option value="">Seleccione un ciclo</option>
          {ciclos.map((item) => (
            <option key={item.id} value={item.id}>{item.tipo} · {item.anio_base}</option>
          ))}
        </select>
      </div>
      {secciones.map((item) => (
        <div className="card mb-3" key={item.seccion}>
          <div className="card-body">
            <label className="form-label fw-semibold" htmlFor={`texto-${item.seccion}`}>{item.descripcion}</label>
            <textarea
              className="form-control"
              id={`texto-${item.seccion}`}
              rows="6"
              disabled={cerrado}
              value={contenidos[item.seccion] ?? ''}
              onChange={(evento) => setContenidos((previo) => ({ ...previo, [item.seccion]: evento.target.value }))}
            />
            <button
              className="btn btn-primary mt-3"
              type="button"
              disabled={cerrado || guardando === item.seccion}
              onClick={() => guardar(item.seccion)}
            >
              {guardando === item.seccion ? 'Guardando...' : 'Guardar texto'}
            </button>
          </div>
        </div>
      ))}
    </section>
  )
}

export default InformeTextos
