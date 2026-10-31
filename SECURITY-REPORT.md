# Security Report: Docker- und Dependency-Härtung

Stand: 2026-10-31

## Änderungen

- Basis auf `python:3.12-slim-trixie` umgestellt und den geprüften Multi-Arch-Index-Digest `sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159` fixiert. Der unverifizierte Standard-Tag wurde dadurch durch Debian 13.7 / Python 3.12.16 ersetzt. Die benötigten Pango-, HarfBuzz- und Schriftpakete bleiben installiert; APT verwendet weiterhin `--no-install-recommends` und entfernt Paketlisten im selben Layer.
- BuildKit-pip-Cache, `pip check` und pip 26.2.2 sind im Docker-Build ergänzt. Anforderungen werden weiterhin vor dem Anwendungscode kopiert.
- UID 1000 (`nk`), beschreibbare `/data`- und `/dokumente`-Pfade, Healthcheck auf `/health`, stdout/stderr-Logging und Gunicorn mit einem Worker/vier Threads bleiben erhalten.
- `.dockerignore` schließt `.env`-Varianten, virtuelle Umgebungen, Datenbanken, Dokumente, private Schlüssel und weitere lokale Metadaten aus.
- Beide Compose-Dateien setzen `init: true` und `no-new-privileges:true`. Volume-Namen, Ports, Umgebungsvariablen und `restart: unless-stopped` sind unverändert. Read-only-Dateisystem, zusätzliche Capability-Reduktion und Ressourcenlimits wurden wegen möglicher Auswirkungen auf SQLite, Uploads und PDF-Erzeugung nicht aktiviert.
- Das Test-Workflow ist wiederverwendbar. Der Tag-Publish-Workflow wartet nun auf die Tests und einen Trivy-Scan für AMD64 und ARM64. JSON-/Text-Berichte werden als 30-Tage-Artefakte bereitgestellt; Critical-Findings mit bekanntem Fix blockieren die Veröffentlichung.

## Dependency-Versionen

| Paket | Vorher | Jetzt |
|---|---:|---:|
| Flask | 3.1.0 | 3.1.3 |
| Gunicorn | 23.0.0 | 23.0.0 (unverändert) |
| WeasyPrint | 62.3 | 70.0 |
| pydyf | 0.10.0 (direkt gepinnt) | 0.13.0 (von WeasyPrint aufgelöst) |
| pypdf | 4.3.1 | 6.21.4 |
| Segno | 1.6.1 | 1.6.1 (unverändert) |
| Pillow | 10.4.0 | 13.0.0 |
| pip im Image | 25.0.1 (Basisimage) | 26.2.2 |

Die angegebenen Paketstände wurden unter Python 3.12 aufgelöst. `pip check` meldet keine Konflikte. Der vorherige pydyf-Pin wurde entfernt, damit die von WeasyPrint definierte kompatible Version installiert wird.

## Verifizierung

| Prüfung | Ergebnis |
|---|---|
| `docker build --pull --no-cache -t immobilienverwalter:security-test .` | Erfolgreich, finaler Digest-gepinnter Build |
| `pip check` im Image | Erfolgreich: keine fehlerhaften Anforderungen |
| `python -m pytest -q tests -p no:cacheprovider` im finalen Image | Erfolgreich: 13 Tests bestanden |
| Health-Endpunkt im laufenden Container | HTTP 200, JSON-Status `ok` |
| Laufzeitbenutzer | `nk` (UID 1000) |
| Daten-/Dokumenten-Schreibzugriff und Neustart | Erfolgreich mit eigens angelegten Test-Volumes; Testvolumes danach entfernt |
| `docker compose config -q` für beide Compose-Dateien | Erfolgreich |
| actionlint für beide Workflows | Erfolgreich; ShellCheck wurde separat deaktiviert, nachdem es eine bestehende Warnung zur Schleifenvariablen in `tests.yml` angezeigt hatte |
| `pip-audit -r requirements.txt` | Erfolgreich: keine bekannten Schwachstellen |
| Trivy 0.76.1, vollständiger Vulnerability-Scan | 0 Findings im finalen Image (Debian und Python-Pakete) |
| Grype 0.121.0, vollständiger Scan | 180 Paketmatches, 85 eindeutige Vulnerability-IDs: 61 High, 63 Medium, 12 Low, 50 Negligible, 0 Critical |
| ARM64-Anwendungsimage lokal | Nicht abschließend verifiziert; ein lokaler Cross-Build wurde durch fehlende QEMU-Emulation zunächst abgebrochen, die Emulation danach eingerichtet. Der Wiederholungslauf wurde nicht abgeschlossen. Das Python-Trixie-Basismanifest enthält `linux/arm64/v8`; CI baut und scannt ARM64 separat. |

Die Integrationstests prüfen unter anderem Einrichtung/Anmeldung, Health/SQLite, CSRF, Zwei-Faktor-Funktionen, Dateien/Bilder sowie PDF-Export und -Zusammenführung. Der PDF-Test bestätigt ein Ergebnis mit vier Seiten (Abrechnung plus PDF- und JPG-Beleg). Ein SMTP-Server wurde nicht eingebunden; realer E-Mail-Versand und parallele Erinnerungsthreads wurden nicht manuell getestet. Das visuelle PDF-Layout für alle Schriftarten, Umlaute und Seitenumbrüche wurde nicht manuell geprüft.

## Scannervergleich

Der bereitgestellte Ausgangsbericht vom 2026-10-31 nennt für `ghcr.io/bitnike/immobilienverwalter:latest`:

| Scanner | Critical | High | Medium | Low | Negligible | Unknown |
|---|---:|---:|---:|---:|---:|---:|
| Grype | 4 | 116 | 123 | 18 | 50 | 0 |
| Trivy | 4 | 99 | 131 | 71 | 0 | 4 |

Nach den Änderungen meldet Trivy 0 Findings über alle erkannten Schweregrade. Grype meldet 0 Critical und keine Python-Paket-Findings mehr. Seine verbleibenden Matches sind:

| Pakettyp | Schweregrad | Matches | Fix laut Grype |
|---|---|---:|---|
| Debian | High | 61 | keiner bekannt |
| Debian | Medium | 53 | keiner bekannt |
| Debian | Low | 10 | keiner bekannt |
| Debian | Negligible | 49 | keiner bekannt |
| Binary | Medium | 5 | verfügbar |
| Binary | Low | 1 | verfügbar |
| Binary | Negligible | 1 | verfügbar |
| Python | alle | 0 | nicht zutreffend |

Grype zählt Matches je Paket und nicht ausschließlich CVE-IDs; daher sind 180 Matches nicht gleich 180 eindeutigen Schwachstellen. Die 85 eindeutigen IDs enthalten auch überlappende Paketzuordnungen. Trivy und Grype verwenden unterschiedliche Advisory- und Severity-Zuordnungen und ihre Zählwerte sind nicht additiv. Die aktuelle Scan-Auswertung wurde lokal am selben Image-Tag ausgeführt; die Report-Metadaten dokumentieren nicht den Image-Digest und Scanner-Datenbankstände sind zeitabhängig.

## Offene Risiken und Bewertung

- Grype kennzeichnet 61 High-Findings in Debian-Paketen als ohne bekannten Fix. Diese stammen aus dem Debian-Trixie-Basisimage und den benötigten nativen Laufzeitbibliotheken. Es wurde kein Finding unterdrückt. Die Pakete sind weiterhin Teil der Anwendungslaufzeit; daher werden sie nicht pauschal als unerreichbar oder False Positive eingestuft. Bei Bereitstellung eines Debian-Fixes sollte der gepinnte Basisdigest aktualisiert und neu gebaut/gescannt werden.
- Trivy meldet für dieselbe Image-Version keine Vulnerabilities. Der Unterschied wird nicht als Entwarnung für die Grype-Meldungen interpretiert; die Scannerdatenbanken und Match-Verfahren unterscheiden sich.
- Der Basisdigest erhöht die Reproduzierbarkeit, verhindert aber automatische Aufnahme neuer Upstream-Patches. Digest-Updates müssen regelmäßig geprüft und in einem Build-/Scan-Lauf übernommen werden.
- Der lokale ARM64-App-Build und ein GHCR-Release-Workflow wurden nicht erfolgreich ausgeführt. Die CI-Pipeline ist entsprechend eingerichtet, aber ihr Release-Gate muss beim nächsten GitHub-Actions-Lauf bestätigt werden.
- Manuelle Prüfungen vor Produktivfreigabe: echte E-Mail-Erinnerungen/Einmalversand, visuelle PDF-Stichproben (Umlaute, Tabellen, Fonts, Seitenumbrüche), Upload und Download gegen persistente Volumes sowie Start und Healthcheck auf ARM64-Hardware.

## Mögliche Breaking Changes

- WeasyPrint 70.0 und pypdf 6.21.4 ändern gegenüber den alten Versionen interne APIs und Rendering-/Reader-Verhalten. Die bestehenden PDF-Integrationsfälle bestehen; ein vollständiger visueller Vergleich wurde nicht vorgenommen.
- Debian 13 verwendet neuere native Bibliotheken. Der lokale AMD64-Build und die PDF-Tests waren erfolgreich; ARM64-App-Build und -Laufzeittest bleiben offen.
- Compose `init` und `no-new-privileges` können Prozess-/Privilege-Verhalten einschränken. Der Containerstart und Schreibzugriff auf Test-Volumes waren erfolgreich; vorhandene produktive Volumes wurden nicht berührt.

## Bereitstellungshinweis

Es wurden keine Commits, Pushes, Releases, Produktionsdeployments, Datenbankmigrationen oder Änderungen an bestehenden Volumes ausgeführt. Der lokale Stand ist ein Security-Testimage und kein veröffentlichter Tag.
