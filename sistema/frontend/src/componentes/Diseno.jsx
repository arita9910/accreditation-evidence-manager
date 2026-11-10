import { NavLink } from 'react-router-dom'

function Diseno({ children }) {
  return (
    <div className="app-shell">
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark px-3">
        <span className="navbar-brand mb-0 h1">Acreditación</span>
        <ul className="navbar-nav flex-row gap-3 ms-4">
          <li className="nav-item">
            <NavLink className="nav-link" to="/">Catálogo</NavLink>
          </li>
          <li className="nav-item">
            <NavLink className="nav-link" to="/ciclos">Ciclos</NavLink>
          </li>
          <li className="nav-item">
            <NavLink className="nav-link" to="/auditoria">Auditoría</NavLink>
          </li>
        </ul>
      </nav>
      <main className="container py-4">{children}</main>
    </div>
  )
}

export default Diseno
