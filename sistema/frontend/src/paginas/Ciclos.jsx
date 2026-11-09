import { useEffect, useMemo, useState } from 'react'
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

function ordenarNumeros(valores) {
  return [...valores].sort((a, b) => Number(a) - Number(b))
}

function normalizarCursoInicial(valor) {
  if (valor === null || valor === undefined) {
    return ''
  }

  const texto = String(valor).trim()
  if (!texto) {
    return ''
  }

  const [primerFragmento] = texto.split('-')
  return primerFragmento.replace(/\D/g, '')
}

function Ciclos() {
  const [carreras, setCarreras] = useState([])
  const [ciclos, setCiclos] = useState([])
  const [versiones, setVersiones] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [avisoVersiones, setAvisoVersiones] = useState(null)
  const [mensajeExito, setMensajeExito] = useState('')
  const [erroresApertura, setErroresApertura] = useState([])
  const [errorCierre, setErrorCierre] = useState('')
  const [errorAsignacion, setErrorAsignacion] = useState('')
  const [asignaciones, setAsignaciones] = useState([])
  const [cargandoAsignaciones, setCargandoAsignaciones] = useState(false)
  const [cicloAsignacionesId, setCicloAsignacionesId] = useState('')
  const [formApertura, setFormApertura] = useState({
    carrera: '',
    tipo: '',
    anio_base: '',
    curso_inicial: '',
    version_normativa: '',
    ciclo_anterior: '',
  })
  const [formCierrePorCiclo, setFormCierrePorCiclo] = useState({})
  const [formAsignacion, setFormAsignacion] = useState({
    usuario: '',
    dimension: '',
  })

  const cargarBase = async () => {
    setError(null)
    const [carrerasRespuesta, ciclosRespuesta] = await Promise.all([
      peticion('/api/carreras/'),
      peticion('/api/ciclos/'),
    ])
    setCarreras(extraerLista(carrerasRespuesta))
    setCiclos(extraerLista(ciclosRespuesta))
  }

  useEffect(() => {
    let vigente = true

    Promise.all([cargarBase(), peticion('/api/catalogo/versiones/')])
      .then(([, versionesRespuesta]) => {
        if (!vigente) {
          return
        }
        setVersiones(extraerLista(versionesRespuesta))
        setAvisoVersiones(null)
      })
      .catch(async (errorRecibido) => {
        if (!vigente) {
          return
        }

        if (String(errorRecibido.message).includes('not_found')) {
          setAvisoVersiones(
            'No se pudo cargar el catálogo de versiones. Indica el ID de versión normativa manualmente.',
          )
          try {
            await cargarBase()
          } catch (errorBase) {
            setError(errorBase.message)
          }
          return
        }

        setError(errorRecibido.message)
      })
      .finally(() => {
        if (vigente) {
          setCargando(false)
        }
      })

    return () => {
      vigente = false
    }
  }, [])

  const ciclosPorCarrera = useMemo(() => {
    const mapa = new Map()
    ciclos.forEach((ciclo) => {
      const carreraId = String(ciclo.carrera)
      if (!mapa.has(carreraId)) {
        mapa.set(carreraId, [])
      }
      mapa.get(carreraId).push(ciclo)
    })
    return mapa
  }, [ciclos])

  const ciclosAbiertos = useMemo(
    () => ciclos.filter((ciclo) => ciclo.estado === 'abierto'),
    [ciclos],
  )

  const cursoInicial = formApertura.curso_inicial === '' ? '' : Number(formApertura.curso_inicial)
  const cursoFinalSugerido = cursoInicial === '' || Number.isNaN(cursoInicial) ? '' : cursoInicial + 4

  const cargarAsignaciones = async (cicloId) => {
    if (!cicloId) {
      setAsignaciones([])
      return
    }

    setCargandoAsignaciones(true)
    setErrorAsignacion('')
    try {
      const respuesta = await peticion(`/api/ciclos/${cicloId}/asignaciones/`)
      setAsignaciones(extraerLista(respuesta))
    } catch (errorRecibido) {
      setErrorAsignacion(errorRecibido.message)
      setAsignaciones([])
    } finally {
      setCargandoAsignaciones(false)
    }
  }

  const validarApertura = () => {
    const errores = []
    const cursoInicialNumero = Number(formApertura.curso_inicial)

    if (!formApertura.carrera) {
      errores.push('Debe seleccionar una carrera.')
    }
    if (!formApertura.tipo.trim()) {
      errores.push('Debe indicar el tipo de ciclo.')
    }
    if (!formApertura.anio_base) {
      errores.push('Debe indicar el año base.')
    }
    if (!formApertura.curso_inicial || !Number.isInteger(cursoInicialNumero) || cursoInicialNumero <= 0) {
      errores.push('Debe indicar el curso inicial.')
    }
    if (!formApertura.version_normativa) {
      errores.push('Debe indicar la versión normativa.')
    }

    return errores
  }

  const recargarTrasCambio = async () => {
    await cargarBase()
    if (cicloAsignacionesId) {
      await cargarAsignaciones(cicloAsignacionesId)
    }
  }

  const enviarApertura = async (evento) => {
    evento.preventDefault()
    setMensajeExito('')
    setErrorCierre('')
    setErrorAsignacion('')
    const errores = validarApertura()
    setErroresApertura(errores)
    if (errores.length > 0) {
      return
    }

    const cursoInicialNumero = Number(formApertura.curso_inicial)
    if (!Number.isInteger(cursoInicialNumero) || cursoInicialNumero <= 0) {
      setErroresApertura(['Debe indicar un curso inicial válido.'])
      return
    }

    const cuerpo = {
      carrera: Number(formApertura.carrera),
      tipo: formApertura.tipo.trim(),
      anio_base: Number(formApertura.anio_base),
      curso_inicial: cursoInicialNumero,
      version_normativa: Number(formApertura.version_normativa),
    }
    if (formApertura.ciclo_anterior) {
      cuerpo.ciclo_anterior = Number(formApertura.ciclo_anterior)
    }

    try {
      await peticion('/api/ciclos/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cuerpo),
      })
      setErroresApertura([])
      setMensajeExito('Ciclo abierto correctamente.')
      await recargarTrasCambio()
    } catch (errorRecibido) {
      setErroresApertura([errorRecibido.message])
    }
  }

  const enviarCierre = async (cicloId) => {
    setMensajeExito('')
    setErrorCierre('')
    const datos = formCierrePorCiclo[cicloId] || { categoria: '', vigencia: '' }
    const cuerpo = {}
    if (datos.categoria?.trim()) {
      cuerpo.categoria_obtenida = datos.categoria.trim()
    }
    if (datos.vigencia) {
      cuerpo.vigencia_anios = Number(datos.vigencia)
    }

    try {
      await peticion(`/api/ciclos/${cicloId}/cerrar/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cuerpo),
      })
      setMensajeExito('Ciclo cerrado correctamente.')
      await recargarTrasCambio()
    } catch (errorRecibido) {
      setErrorCierre(errorRecibido.message)
    }
  }

  const enviarAsignacion = async (evento) => {
    evento.preventDefault()
    setMensajeExito('')
    setErrorAsignacion('')
    if (!cicloAsignacionesId) {
      setErrorAsignacion('Debe seleccionar un ciclo abierto para gestionar asignaciones.')
      return
    }
    if (!formAsignacion.usuario || !formAsignacion.dimension) {
      setErrorAsignacion('Debe indicar usuario y dimensión.')
      return
    }

    try {
      await peticion(`/api/ciclos/${cicloAsignacionesId}/asignaciones/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          usuario: Number(formAsignacion.usuario),
          dimension: Number(formAsignacion.dimension),
        }),
      })
      setMensajeExito('Asignación registrada correctamente.')
      await cargarAsignaciones(cicloAsignacionesId)
    } catch (errorRecibido) {
      setErrorAsignacion(errorRecibido.message)
    }
  }

  const quitarAsignacion = async (asignacion) => {
    setMensajeExito('')
    setErrorAsignacion('')
    try {
      await peticion(`/api/ciclos/${cicloAsignacionesId}/asignaciones/`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          usuario: asignacion.usuario,
          dimension: asignacion.dimension,
        }),
      })
      setMensajeExito('Asignación eliminada correctamente.')
      await cargarAsignaciones(cicloAsignacionesId)
    } catch (errorRecibido) {
      setErrorAsignacion(errorRecibido.message)
    }
  }

  const usuariosTabla = ordenarNumeros(new Set(asignaciones.map((item) => item.usuario)))
  const dimensionesTabla = ordenarNumeros(new Set(asignaciones.map((item) => item.dimension)))

  if (cargando) {
    return <Cargando texto="Cargando ciclos..." />
  }

  if (error) {
    return <Mensaje tipo="error" titulo="No se pudo cargar el módulo de ciclos.">{error}</Mensaje>
  }

  return (
    <section aria-labelledby="titulo-ciclos" className="d-grid gap-4">
      <header>
        <h1 id="titulo-ciclos">Gestión de ciclos por carrera</h1>
        <p className="text-body-secondary mb-0">
          Administra la apertura, cierre y la asignación de dimensiones por usuario.
        </p>
      </header>

      {mensajeExito ? <Mensaje tipo="success">{mensajeExito}</Mensaje> : null}
      {avisoVersiones ? <Mensaje tipo="warning">{avisoVersiones}</Mensaje> : null}

      <section aria-labelledby="titulo-lista-carreras" className="card">
        <div className="card-body">
          <h2 id="titulo-lista-carreras" className="h5">Carreras y estado de ciclos</h2>
          <div className="table-responsive">
            <table className="table table-sm align-middle">
              <thead>
                <tr>
                  <th scope="col">Carrera</th>
                  <th scope="col">Activa</th>
                  <th scope="col">Ciclos</th>
                </tr>
              </thead>
              <tbody>
                {carreras.map((carrera) => {
                  const ciclosCarrera = ciclosPorCarrera.get(String(carrera.id)) ?? []
                  return (
                    <tr key={carrera.id}>
                      <td>{carrera.nombre}</td>
                      <td>{carrera.activa ? 'Sí' : 'No'}</td>
                      <td>
                        {ciclosCarrera.length === 0 ? (
                          <span className="text-body-secondary">Sin ciclos registrados</span>
                        ) : (
                          <ul className="list-unstyled mb-0">
                            {ciclosCarrera.map((ciclo) => (
                              <li key={ciclo.id}>
                                <span>
                                  {ciclo.tipo} {ciclo.anio_base} ({ciclo.curso_inicial}-{ciclo.curso_final})
                                </span>
                                <span
                                  className={`badge ms-2 ${
                                    ciclo.estado === 'abierto' ? 'text-bg-success' : 'text-bg-secondary'
                                  }`}
                                >
                                  {ciclo.estado}
                                </span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section aria-labelledby="titulo-apertura" className="card">
        <div className="card-body">
          <h2 id="titulo-apertura" className="h5">Abrir ciclo</h2>
          <Mensaje tipo="info">
            La apertura exige cinco cursos consecutivos. El curso final se calculará como curso inicial + 4.
          </Mensaje>
          {erroresApertura.length > 0 ? (
            <Mensaje tipo="error" titulo="Revisa el formulario de apertura.">
              <ul className="mb-0 mt-2">
                {erroresApertura.map((errorItem) => <li key={errorItem}>{errorItem}</li>)}
              </ul>
            </Mensaje>
          ) : null}

          <form className="row g-3" onSubmit={enviarApertura}>
            <div className="col-md-6">
              <label className="form-label" htmlFor="carrera-apertura">Carrera</label>
              <select
                className="form-select"
                id="carrera-apertura"
                value={formApertura.carrera}
                onChange={(evento) => setFormApertura((previo) => ({ ...previo, carrera: evento.target.value }))}
              >
                <option value="">Seleccione</option>
                {carreras.map((carrera) => (
                  <option key={carrera.id} value={carrera.id}>{carrera.nombre}</option>
                ))}
              </select>
            </div>

            <div className="col-md-6">
              <label className="form-label" htmlFor="tipo-apertura">Tipo</label>
              <select
                className="form-select"
                id="tipo-apertura"
                value={formApertura.tipo}
                onChange={(evento) => setFormApertura((previo) => ({ ...previo, tipo: evento.target.value }))}
              >
                <option value="">Seleccione</option>
                <option value="autoevaluación">autoevaluación</option>
                <option value="acreditación">acreditación</option>
                <option value="reacreditación">reacreditación</option>
              </select>
            </div>

            <div className="col-md-4">
              <label className="form-label" htmlFor="anio-base-apertura">Año base</label>
              <input
                className="form-control"
                id="anio-base-apertura"
                inputMode="numeric"
                value={formApertura.anio_base}
                onChange={(evento) => setFormApertura((previo) => ({ ...previo, anio_base: evento.target.value }))}
              />
            </div>

            <div className="col-md-4">
              <label className="form-label" htmlFor="curso-inicial-apertura">Curso inicial</label>
              <input
                className="form-control"
                id="curso-inicial-apertura"
                type="text"
                inputMode="numeric"
                maxLength={4}
                pattern="[0-9]{4}"
                placeholder="2024"
                value={formApertura.curso_inicial}
                onChange={(evento) => setFormApertura((previo) => ({
                  ...previo,
                  curso_inicial: normalizarCursoInicial(evento.target.value),
                }))}
              />
            </div>

            <div className="col-md-4">
              <label className="form-label" htmlFor="curso-final-sugerido">Curso final esperado</label>
              <input
                className="form-control"
                id="curso-final-sugerido"
                readOnly
                value={cursoFinalSugerido}
              />
            </div>

            <div className="col-md-6">
              <label className="form-label" htmlFor="version-apertura">Versión normativa</label>
              {versiones.length > 0 ? (
                <select
                  className="form-select"
                  id="version-apertura"
                  value={formApertura.version_normativa}
                  onChange={(evento) => setFormApertura((previo) => ({
                    ...previo,
                    version_normativa: evento.target.value,
                  }))}
                >
                  <option value="">Seleccione</option>
                  {versiones.map((version) => (
                    <option key={version.id} value={version.id}>{version.nombre}</option>
                  ))}
                </select>
              ) : (
                <input
                  className="form-control"
                  id="version-apertura"
                  inputMode="numeric"
                  value={formApertura.version_normativa}
                  onChange={(evento) => setFormApertura((previo) => ({
                    ...previo,
                    version_normativa: evento.target.value,
                  }))}
                />
              )}
            </div>

            <div className="col-md-6">
              <label className="form-label" htmlFor="ciclo-anterior-apertura">Ciclo anterior (opcional)</label>
              <select
                className="form-select"
                id="ciclo-anterior-apertura"
                value={formApertura.ciclo_anterior}
                onChange={(evento) => setFormApertura((previo) => ({
                  ...previo,
                  ciclo_anterior: evento.target.value,
                }))}
              >
                <option value="">Sin ciclo anterior</option>
                {ciclos
                  .filter((ciclo) => ciclo.estado === 'cerrado')
                  .map((ciclo) => (
                    <option key={ciclo.id} value={ciclo.id}>
                      #{ciclo.id} · {ciclo.tipo} {ciclo.anio_base}
                    </option>
                  ))}
              </select>
            </div>

            <div className="col-12">
              <button className="btn btn-primary" type="submit">Abrir ciclo</button>
            </div>
          </form>
        </div>
      </section>

      <section aria-labelledby="titulo-cierre" className="card">
        <div className="card-body">
          <h2 id="titulo-cierre" className="h5">Cerrar ciclo</h2>
          {errorCierre ? <Mensaje tipo="error">{errorCierre}</Mensaje> : null}
          {ciclosAbiertos.length === 0 ? (
            <Mensaje tipo="info">No hay ciclos abiertos para cerrar.</Mensaje>
          ) : (
            <div className="d-grid gap-3">
              {ciclosAbiertos.map((ciclo) => (
                <div className="border rounded p-3" key={ciclo.id}>
                  <p className="mb-2">
                    <strong>#{ciclo.id}</strong> · {ciclo.tipo} {ciclo.anio_base}
                  </p>
                  <div className="row g-2">
                    <div className="col-md-5">
                      <label className="form-label" htmlFor={`categoria-cierre-${ciclo.id}`}>
                        Categoría (opcional)
                      </label>
                      <input
                        className="form-control"
                        id={`categoria-cierre-${ciclo.id}`}
                        value={formCierrePorCiclo[ciclo.id]?.categoria ?? ''}
                        onChange={(evento) => setFormCierrePorCiclo((previo) => ({
                          ...previo,
                          [ciclo.id]: {
                            ...(previo[ciclo.id] || {}),
                            categoria: evento.target.value,
                          },
                        }))}
                      />
                    </div>
                    <div className="col-md-4">
                      <label className="form-label" htmlFor={`vigencia-cierre-${ciclo.id}`}>
                        Vigencia (opcional)
                      </label>
                      <select
                        className="form-select"
                        id={`vigencia-cierre-${ciclo.id}`}
                        value={formCierrePorCiclo[ciclo.id]?.vigencia ?? ''}
                        onChange={(evento) => setFormCierrePorCiclo((previo) => ({
                          ...previo,
                          [ciclo.id]: {
                            ...(previo[ciclo.id] || {}),
                            vigencia: evento.target.value,
                          },
                        }))}
                      >
                        <option value="">Sin vigencia</option>
                        <option value="5">5</option>
                        <option value="7">7</option>
                        <option value="9">9</option>
                      </select>
                    </div>
                    <div className="col-md-3 d-flex align-items-end">
                      <button
                        className="btn btn-outline-primary w-100"
                        onClick={() => enviarCierre(ciclo.id)}
                        type="button"
                      >
                        Cerrar ciclo
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section aria-labelledby="titulo-asignaciones" className="card">
        <div className="card-body">
          <h2 id="titulo-asignaciones" className="h5">Asignación dimensión × usuario</h2>
          {errorAsignacion ? <Mensaje tipo="error">{errorAsignacion}</Mensaje> : null}

          <div className="row g-3 align-items-end mb-3">
            <div className="col-md-6">
              <label className="form-label" htmlFor="ciclo-asignaciones">Ciclo abierto</label>
              <select
                className="form-select"
                id="ciclo-asignaciones"
                value={cicloAsignacionesId}
                onChange={(evento) => {
                  const nuevoId = evento.target.value
                  setCicloAsignacionesId(nuevoId)
                  cargarAsignaciones(nuevoId)
                }}
              >
                <option value="">Seleccione</option>
                {ciclosAbiertos.map((ciclo) => (
                  <option key={ciclo.id} value={ciclo.id}>
                    #{ciclo.id} · {ciclo.tipo} {ciclo.anio_base}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <form className="row g-3 mb-3" onSubmit={enviarAsignacion}>
            <div className="col-md-4">
              <label className="form-label" htmlFor="usuario-asignacion">Usuario (ID)</label>
              <input
                className="form-control"
                id="usuario-asignacion"
                inputMode="numeric"
                value={formAsignacion.usuario}
                onChange={(evento) => setFormAsignacion((previo) => ({ ...previo, usuario: evento.target.value }))}
              />
            </div>
            <div className="col-md-4">
              <label className="form-label" htmlFor="dimension-asignacion">Dimensión (ID)</label>
              <input
                className="form-control"
                id="dimension-asignacion"
                inputMode="numeric"
                value={formAsignacion.dimension}
                onChange={(evento) => setFormAsignacion((previo) => ({ ...previo, dimension: evento.target.value }))}
              />
            </div>
            <div className="col-md-4 d-flex align-items-end">
              <button className="btn btn-primary w-100" type="submit">Agregar asignación</button>
            </div>
          </form>

          {cargandoAsignaciones ? (
            <Cargando texto="Cargando asignaciones..." />
          ) : (
            <>
              {dimensionesTabla.length === 0 || usuariosTabla.length === 0 ? (
                <Mensaje tipo="info">No hay asignaciones para mostrar en la tabla.</Mensaje>
              ) : (
                <div className="table-responsive">
                  <table className="table table-bordered table-sm">
                    <thead>
                      <tr>
                        <th scope="col">Dimensión \\ Usuario</th>
                        {usuariosTabla.map((usuarioId) => (
                          <th key={usuarioId} scope="col">Usuario #{usuarioId}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {dimensionesTabla.map((dimensionId) => (
                        <tr key={dimensionId}>
                          <th scope="row">Dimensión #{dimensionId}</th>
                          {usuariosTabla.map((usuarioId) => {
                            const existe = asignaciones.some((asignacion) => (
                              asignacion.dimension === dimensionId && asignacion.usuario === usuarioId
                            ))
                            return (
                              <td key={`${dimensionId}-${usuarioId}`} className="text-center">
                                {existe ? '✓' : '—'}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {asignaciones.length > 0 ? (
                <ul className="list-group">
                  {asignaciones.map((asignacion) => (
                    <li className="list-group-item d-flex justify-content-between" key={asignacion.id}>
                      <span>
                        Usuario #{asignacion.usuario} · Dimensión #{asignacion.dimension}
                      </span>
                      <button
                        className="btn btn-sm btn-outline-danger"
                        onClick={() => quitarAsignacion(asignacion)}
                        type="button"
                      >
                        Quitar
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </>
          )}
        </div>
      </section>
    </section>
  )
}

export default Ciclos
