# Reglas del proyecto
- Implementa solo lo que dicen los artefactos del cambio (tasks.md, design.md, specs). Si algo es ambiguo, no inventes: anótalo como pregunta abierta en sistema/docs/decisiones/ y sigue con lo demás.
- Terminología: indicador = 2.º nivel (24); criterio = 3.er nivel (65). No renombres entidades.
- No declares resultados no ejecutados. Marca [x] solo las tareas cuya verificación ejecutaste. Cada plan cierra con pruebas pasando y un avance en sistema/docs/avance/.
- Pruebas solo en SQLite; PostgreSQL queda como pendiente documentado, nunca como hecho (D-14).
- Vitest: npm run test:run -- --pool=vmThreads --maxWorkers=1
- No subas a Git .venv*/, *.sqlite3, node_modules/, .docx ni logs. No añadas dependencias sin que se pida.
- Un cambio a la vez. Si el mismo error se repite dos veces, detente y consulta.
- Al terminar un bloque, detente y da: los comandos de prueba exactos con su resultado y lo que quedó pendiente.
- Escribe artefactos y documentos en español.