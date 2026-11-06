import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Cargando, Mensaje } from '../componentes'
import peticion from '../api/cliente'

const TIPOS_DATO = {
  cuantitativo: 'Cuantitativo',
  cualitativo: 'Cualitativo',
}

function coincide(texto, consulta) {
  return String(texto ?? '').toLocaleLowerCase('es').includes(consulta)
}

function Catalogo() {
  const [catalogo, setCatalogo] = useState(null)
  const [consulta, setConsulta] = useState('')
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let vigente = true

    peticion('/api/catalogo/')
      .then((datos) => {
        if (vigente) {
          setCatalogo(datos)
        }
      })
      .catch((errorRecibido) => {
        if (vigente) {
          setError(errorRecibido.message)
        }
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

  if (cargando) {
    return <Cargando texto="Cargando catálogo..." />
  }

  if (error) {
    return <Mensaje tipo="error" titulo="No se pudo cargar el catálogo">{error}</Mensaje>
  }

  const termino = consulta.trim().toLocaleLowerCase('es')
  const dimensiones = (catalogo?.dimensiones ?? [])
    .map((dimension) => {
      const dimensionCoincide = coincide(
        `${dimension.codigo} ${dimension.nombre}`,
        termino,
      )
      const indicadores = (dimension.indicadores ?? [])
        .map((indicador) => {
          const indicadorCoincide = coincide(
            `${indicador.codigo} ${indicador.texto}`,
            termino,
          )
          const criterios = (indicador.criterios ?? []).filter((criterio) => (
            !termino
            || dimensionCoincide
            || indicadorCoincide
            || coincide(`${criterio.codigo} ${criterio.texto}`, termino)
          ))

          return { ...indicador, criterios }
        })
        .filter((indicador) => indicador.criterios.length > 0)

      return { ...dimension, indicadores }
    })
    .filter((dimension) => dimension.indicadores.length > 0)

  const cantidadCriterios = dimensiones.reduce(
    (total, dimension) => total + dimension.indicadores.reduce(
      (subtotal, indicador) => subtotal + indicador.criterios.length,
      0,
    ),
    0,
  )

  return (
    <section aria-labelledby="titulo-catalogo">
      <header className="mb-4">
        <h1 id="titulo-catalogo">Catálogo normativo SEA-CU 2025</h1>
        <p className="text-body-secondary">
          Explora las dimensiones, indicadores y criterios de la versión disponible.
        </p>
        {catalogo?.version ? (
          <p className="mb-0">
            <strong>Versión:</strong> {catalogo.version.nombre}
          </p>
        ) : null}
      </header>

      <div className="mb-4">
        <label className="form-label" htmlFor="buscar-criterio">
          Buscar por código o texto
        </label>
        <input
          className="form-control"
          id="buscar-criterio"
          onChange={(evento) => setConsulta(evento.target.value)}
          placeholder="Ej.: 3.2.4 o texto del criterio"
          type="search"
          value={consulta}
        />
      </div>

      {dimensiones.length === 0 ? (
        <Mensaje tipo="info">No se encontraron criterios para la búsqueda.</Mensaje>
      ) : (
        <>
          <p aria-live="polite" className="text-body-secondary">
            {dimensiones.length} dimensiones · {cantidadCriterios} criterios
          </p>
          <div aria-label="Árbol del catálogo" className="d-grid gap-2">
            {dimensiones.map((dimension) => (
              <details className="border rounded p-3" key={dimension.codigo} open={Boolean(termino)}>
                <summary className="fw-semibold">
                  {dimension.codigo} {dimension.nombre}
                  <span className="badge text-bg-light ms-2">
                    {dimension.indicadores.length} indicadores
                  </span>
                </summary>
                <div className="mt-3 ps-2">
                  {dimension.indicadores.map((indicador) => (
                    <details
                      className="mb-2"
                      key={indicador.codigo}
                      open={Boolean(termino)}
                    >
                      <summary>
                        <strong>{indicador.codigo}</strong> — {indicador.texto}
                        <span className="badge text-bg-light ms-2">
                          {indicador.criterios.length} criterios
                        </span>
                      </summary>
                      <ul className="mt-2">
                        {indicador.criterios.map((criterio) => (
                          <li className="mb-2" key={criterio.codigo}>
                            <Link to={`/criterios/${encodeURIComponent(criterio.codigo)}`}>
                              {criterio.codigo} — {criterio.texto}
                            </Link>
                            <div className="d-flex flex-wrap gap-2 mt-1">
                              <span className="badge text-bg-secondary">
                                {TIPOS_DATO[criterio.tipo_dato] ?? criterio.tipo_dato}
                              </span>
                              {criterio.solo_en_guia ? (
                                <span className="badge text-bg-warning">
                                  Solo en la Guía
                                </span>
                              ) : null}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </details>
                  ))}
                </div>
              </details>
            ))}
          </div>
        </>
      )}
    </section>
  )
}

export default Catalogo
