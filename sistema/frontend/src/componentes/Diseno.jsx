function Diseno({ children }) {
  return (
    <div className="app-shell">
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark px-3">
        <span className="navbar-brand mb-0 h1">Acreditación</span>
      </nav>
      <main className="container py-4">{children}</main>
    </div>
  )
}

export default Diseno
