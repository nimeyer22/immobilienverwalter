"""Explizite Betriebsbefehle; Web-Imports verändern weder Schema noch Scheduler-Zustand."""
import argparse
import logging
import time
from datetime import date

import db


def migrate(_args):
    db.init_db()
    print(f"Datenbankschema ist auf Version {db.schema_version()}.")


def reminders(_args):
    # main registriert alle Routen und stellt denselben App-Kontext wie gunicorn bereit.
    from main import app
    from vertraege import pruefen

    with app.app_context():
        count = pruefen(date.today())
    print(f"{count} Termin(e) gemeldet.")


def reminders_loop(args):
    """Ein einzelner Scheduler-Prozess für Compose; Kubernetes verwendet stattdessen einen CronJob."""
    while True:
        try:
            reminders(args)
        except Exception:  # noqa: BLE001 - nächster Lauf soll weiterhin stattfinden
            logging.exception("Erinnerungslauf fehlgeschlagen")
        time.sleep(args.interval)


def main():
    parser = argparse.ArgumentParser(description="Betriebsbefehle für Immobilienverwalter")
    commands = parser.add_subparsers(required=True)
    commands.add_parser("migrate", help="Datenbankschema einmalig aktualisieren").set_defaults(func=migrate)
    commands.add_parser("reminders", help="Fällige Erinnerungen einmalig versenden").set_defaults(func=reminders)
    loop = commands.add_parser("reminders-loop", help="Erinnerungen periodisch in eigenem Prozess prüfen")
    loop.add_argument("--interval", type=int, default=6 * 3600, help="Abstand in Sekunden (Standard: 21600)")
    loop.set_defaults(func=reminders_loop)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    args.func(args)


if __name__ == "__main__":
    main()
