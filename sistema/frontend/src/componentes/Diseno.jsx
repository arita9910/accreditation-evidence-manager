import { NavLink } from 'react-router-dom'

function Diseno({ children, onLogout, usuario }) {
  const esAdmin = usuario?.rol === 'administrador_tecnico'
  const autenticado = Boolean(usuario)

  return (
    <div className="app-shell">
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark px-3">
        <span className="navbar-brand mb-0 h1">Acreditación</span>
        <ul className="navbar-nav flex-row gap-3 ms-4 flex-wrap">
          <li className="nav-item">
            <NavLink className="nav-link" to="/">Catálogo</NavLink>
          </li>
          <li className="nav-item">
            <NavLink className="nav-link" to="/ciclos">Ciclos</NavLink>
          </li>
          <li className="nav-item">
            <NavLink className="nav-link" to="/auditoria">Auditoría</NavLink>
          </li>
          {autenticado ? (
            <>
              <li className="nav-item">
                <NavLink className="nav-link" to="/perfil">Perfil</NavLink>
              </li>
              {esAdmin ? (
                <li className="nav-item">
                  <NavLink className="nav-link" to="/usuarios">Usuarios</NavLink>
                </li>
              ) : null}
            </>
          ) : null}
        </ul>

        <div className="ms-auto d-flex align-items-center gap-2">
          {autenticado ? (
            <>
              <span className="text-light small">{usuario?.username}</span>
              <button className="btn btn-outline-light btn-sm" onClick={onLogout} type="button">
                Cerrar sesión
              </button>
            </>
          ) : (
            <NavLink className="btn btn-outline-light btn-sm" to="/login">
              Iniciar sesión
            </NavLink>
          )}
        </div>
      </nav>
      <main className="container py-4">{children}</main>
    </div>
  )
}

export default Diseno
