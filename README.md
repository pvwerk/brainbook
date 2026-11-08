# Werkzeuge

Eigene Claude-Code-Erweiterungen. Dieses Verzeichnis ist gleichzeitig ein
lokaler Plugin-Marktplatz (`jan-werkzeuge`).

## Enthalten

- **[landkarte](landkarte/)** — kartografiert alle Projekte und schreibt mit,
  was daran getan wurde.

## Einrichten

```sh
claude plugin marketplace add ~/Projekte/werkzeuge
claude plugin install landkarte@jan-werkzeuge
~/Projekte/werkzeuge/landkarte/bin/landkarte einrichten
landkarte regal
```
