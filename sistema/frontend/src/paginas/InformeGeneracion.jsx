import { useEffect, useMemo, useState } from 'react'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

function extraerLista(respuesta) {
  if (Array.isArray(respuesta)) return respuesta
  if (Array.isArray(respuesta?.results)) return respuesta.results
  return []
}

function InformeGeneracion({ usuario }) {
  const autorizado = usuario?.rol === 'administrador_tecnico' || usuario?.rol === 'director_carrera'
  const [ciclos, setCiclos] = useState([])
  const [cicloId, setCicloId] = useState('')
  const [completitud, setCompletitud] = useState(null)
  const [versiones, setVersiones] = useState([])
  const [generando, setGenerando] = useState(false)
  const [cargando, setCargando] = useState(autorizado)
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
    Promise.all([
      peticion(`/api/ciclos/${cicloId}/completitud/`),
      peticion(`/api/ciclos/${cicloId}/informe/versiones/`),
    ])
      .then(([completitudRespuesta, versionesRespuesta]) => {
        if (!vigente) return
        setCompletitud(completitudRespuesta)
        setVersiones(extraerLista(versionesRespuesta?.versiones))
      })
      .catch((errorRecibido) => vigente && setError(errorRecibido.message))
    return () => { vigente = false }
  }, [cicloId])

  const avisos = useMemo(() => {
    if (!completitud) return []
    if (Array.isArray(completitud.avisos)) return completitud.avisos
    if (Array.isArray(completitud.mensajes)) return completitud.mensajes
    return Object.entries(completitud)
      .filter(([clave, valor]) => /aviso|faltante|sin_/i.test(clave) && Boolean(valor))
      .map(([clave, valor]) => Array.isArray(valor) ? `${clave}: ${valor.join(', ')}` : `${clave}: ${valor}`)
  }, [completitud])

  const generar = async () => {
    setGenerando(true)
    setError('')
    setMensaje('')
    try {
      const creada = await peticion(`/api/ciclos/${cicloId}/informe/generar/`, { method: 'POST' })
      setMensaje(`Versión ${creada.numero} generada correctamente.`)
      const respuesta = await peticion(`/api/ciclos/${cicloId}/informe/versiones/`)
      setVersiones(extraerLista(respuesta?.versiones))
    } catch (errorRecibido) {
      setError(errorRecibido.message)
    } finally {
      setGenerando(false)
    }
  }

  if (!autorizado) {
    return <Mensaje tipo="error" titulo="Acceso denegado">Tu rol no permite generar informes.</Mensaje>
  }
  if (cargando) return <Cargando texto="Cargando generación de informes..." />

  const ciclo = ciclos.find((item) => String(item.id) === String(cicloId))
  const cerrado = ciclo?.estado === 'cerrado'

  return (
    <section aria-labelledby="titulo-informe-generacion">
      <h1 id="titulo-informe-generacion">Generación de informe</h1>
      {error ? <Mensaje tipo="error" titulo="Error">{error}</Mensaje> : null}
      {mensaje ? <Mensaje tipo="success" titulo="Informe generado">{mensaje}</Mensaje> : null}
      <div className="mb-4">
        <label className="form-label" htmlFor="generacion-ciclo">Ciclo</label>
        <select className="form-select" id="generacion-ciclo" value={cicloId} onChange={(evento) => setCicloId(evento.target.value)}>
          <option value="">Seleccione un ciclo</option>
          {ciclos.map((item) => (
            <option key={item.id} value={item.id}>{item.tipo} · {item.anio_base}</option>
          ))}
        </select>
      </div>
      {cerrado ? <Mensaje tipo="warning" titulo="Ciclo cerrado">La generación requiere un ciclo abierto.</Mensaje> : null}
      {avisos.length > 0 ? (
        <Mensaje tipo="warning" titulo="Avisos de completitud">
          <ul className="mb-0">
            {avisos.map((aviso, indice) => <li key={`${indice}-${String(aviso)}`}>{String(aviso)}</li>)}
          </ul>
        </Mensaje>
      ) : null}
      <button
        className="btn btn-primary mb-4"
        type="button"
        disabled={!cicloId || cerrado || generando}
        onClick={generar}
      >
        {generando ? 'Generando...' : 'Generar informe'}
      </button>
      <h2 className="h4">Historial de versiones</h2>
      {versiones.length === 0 ? <Mensaje tipo="info">Aún no existen versiones generadas.</Mensaje> : (
        <div className="table-responsive">
          <table className="table align-middle">
            <thead><tr><th>Versión</th><th>Páginas</th><th>Método</th><th>Acciones</th></tr></thead>
            <tbody>
              {versiones.map((version) => (
                <tr key={version.id}>
                  <td>v{version.numero}</td>
                  <td>{version.paginas ?? '—'}</td>
                  <td>{version.metodo_conteo ?? '—'}</td>
                  <td>
                    <a className="btn btn-outline-primary btn-sm" href={`/api/informes/versiones/${version.id}/descarga/`}>
                      Descargar
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default InformeGeneracion
