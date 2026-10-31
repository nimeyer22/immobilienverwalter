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

## Noch nicht produktionsreif für PostgreSQL

Der aktuelle Datenzugriff und die 22 Schemamigrationen sind weiterhin SQLite-spezifisch. `DATABASE_URL` wird
deshalb bewusst noch nicht akzeptiert: Eine bloße DSN-Umschaltung würde unter anderem bei Platzhaltern,
generierten IDs, Collations und Nullvergleichen fehlschlagen. Vor einem PostgreSQL-Rollout fehlen noch:

1. PostgreSQL-native, versionierte Schema-Migrationen und eine Connection-/Transaktionsschicht.
2. Die systematische Portierung aller Abfragen und ein Offline-Importer mit Sequenzabgleich und Validierung.
3. Eine PostgreSQL-gestützte Claim-/Outbox-Logik für wiederholbare Reminder-Läufe.
4. PostgreSQL-Integrationstests in CI sowie Tests mit Verbindungsverlust und parallelen Instanzen.
5. RWX-Speicher oder Object Storage für Dokumente, Fotos und Logos.

Bis dahin bleibt der Betrieb auf eine Web-Replik und gemeinsamen lokalen Speicher beschränkt.
