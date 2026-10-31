# PostgreSQL und Kubernetes

## Umgesetzte Grundlage

Die Web-App hat beim Import keine betrieblichen Seiteneffekte mehr: Sie migriert das Schema nicht und startet
keinen lokalen Scheduler. Migrationen werden mit `python manage.py migrate` ausgeführt, ein Erinnerungslauf mit
`python manage.py reminders`. Compose betreibt dafür getrennte Dienste. `/live` ist eine reine Prozessprobe,
`/ready` prüft Datenbank und aktuelle Schemaversion. `SECRET_KEY` muss bei mehreren Replikaten als identisches
Kubernetes Secret gesetzt werden.

Beispiel für die Probe-Konfiguration eines späteren Deployments:

```yaml
livenessProbe:
  httpGet: {path: /live, port: 8080}
readinessProbe:
  httpGet: {path: /ready, port: 8080}
```

Migrationen gehören in einen einmaligen Release-Job vor das Deployment. Erinnerungen gehören in einen CronJob,
der `python manage.py reminders` startet. Mehrere Scheduler dürfen erst aktiviert werden, wenn die geplante
PostgreSQL-Claim-/Outbox-Sperre umgesetzt ist.

## Datenbankmodus wählen

Ohne `DATABASE_URL` verwendet die Anwendung weiterhin SQLite in `/data/nebenkosten.sqlite`. Das ist der
unkomplizierte interne Modus für genau eine App-Instanz. Für PostgreSQL wird in `.env` beispielsweise gesetzt:

```dotenv
DATABASE_URL=postgresql://immobilienverwalter:passwort@db.example.de:5432/immobilienverwalter?sslmode=require
SECRET_KEY=ein-langer-zufaelliger-und-in-allen-replikaten-identischer-wert
```

Dieselbe Compose-Datei reicht beide Werte aus dem bestehenden `env_file` an Migration, Web-App und Scheduler
weiter. Der PostgreSQL-Server selbst bleibt bewusst extern; Compose provisioniert keine Produktionsdatenbank.
Beim ersten Start legt der Dienst `migrate` das Schema an. Das App-Konto benötigt dafür DDL-Rechte. Für einen
strengeren Produktionsbetrieb sollte ein separates Migrationskonto den Release-Job ausführen und das Web-Konto
nur DML-Rechte besitzen.

PostgreSQL-Migrationen verwenden eine Advisory Lock. Dadurch führen zwei versehentlich parallele Release-Jobs
die Schemaänderungen nicht gleichzeitig aus. Ein Wechsel einer bereits gefüllten SQLite-Installation erfolgt
noch nicht automatisch; bis zum SQLite-Importer muss PostgreSQL leer gestartet werden.

## Noch offene Arbeiten

Der Laufzeitpfad, die 22 Schemaänderungen, Bindings, generierten IDs, Nullvergleiche und case-insensitive
Benutzernamen sind für PostgreSQL unterstützt. Vor einem vollständigen Produktions-Cutover fehlen noch:

1. Ein Offline-Importer für bestehende SQLite-Daten mit Sequenzabgleich und Validierungsbericht.
2. Eine PostgreSQL-gestützte Claim-/Outbox-Logik für wiederholbare Reminder-Läufe.
3. Erweiterte PostgreSQL-Tests für Verbindungsverlust und parallele App-/Scheduler-Instanzen.
4. Eine echte natürliche Sortierung; PostgreSQL sortiert die bisherigen `NATUERLICH`-Felder derzeit lexikalisch.
5. RWX-Speicher oder Object Storage für Dokumente, Fotos und Logos.

Mehrere Web-Replikate sind erst sinnvoll, wenn alle Replikate denselben Dokument-/Bildspeicher und dasselbe
`SECRET_KEY` verwenden. Der Scheduler bleibt bis zur Claim-/Outbox-Umsetzung auf genau eine Instanz beschränkt.
