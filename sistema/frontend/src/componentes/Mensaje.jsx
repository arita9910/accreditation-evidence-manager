function Mensaje({ tipo = 'info', titulo, children }) {
  const clases = {
    info: 'alert alert-info',
    success: 'alert alert-success',
    warning: 'alert alert-warning',
    error: 'alert alert-danger',
  }

  return (
    <div className={clases[tipo] ?? clases.info} role="alert">
      {titulo ? <strong>{titulo}</strong> : null}
      {titulo && children ? ' ' : null}
      {children}
    </div>
  )
}

export default Mensaje
