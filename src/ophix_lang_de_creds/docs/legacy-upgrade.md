---
title: Upgrade vom alten Credserver
slug: legacy-upgrade
order: 99
section: Anmeldeinformationen
---

Diese Seite beschreibt das Upgrade vom Paket `cred-server` (App-Label `creds`) auf das aktuelle Paket `ophix-creds`. Wenn Sie ophix-creds von Grund auf neu installiert haben, ist diese Seite nicht relevant.

---

## Was sich geändert hat

Das alte `cred-server` und das aktuelle `ophix-creds` sind strukturell inkompatibel — Sie können `migrate` nicht gegen eine alte Datenbank ausführen und erwarten, dass es funktioniert. Die wichtigsten Unterschiede sind:

| Bereich | Alt (`cred-server`) | Neu (`ophix-creds`) |
| --- | --- | --- |
| App-Label | `creds` | `ophix_creds` |
| Tabellennamen | `creds_*` | `ophix_creds_*` / `ophix_core_*` |
| Host-/Client-Modelle | In der App `creds` | In `ophix_core` (ophix-server-base) |
| `secret_json`-Speicherung | Klartext-JSONField | Fernet-verschlüsseltes TextField |
| `ClientCredential` | Nur `enabled`, `notes` | + `can_update`, `can_delete`, `can_share` |

Die Spalten `can_update`, `can_delete` und `can_share` werden alle als `False` importiert — bei der Migration werden keine Berechtigungen eskaliert.

---

## Upgrade-Pfad

Der empfohlene Ansatz ist eine **parallele Migration**: Den alten Server in Betrieb lassen, bis der neue vollständig verifiziert ist, dann stilllegen.

### 1. Neuen Credserver einrichten

Folgen Sie dem Standard-Installationsleitfaden — neue virtuelle Umgebung, neue Datenbank:

```bash
pip install ophix-server-base ophix-creds
ophix-manage configure_install credserver
ophix-manage run_install credserver
sudo bash credserver_sudo_install.sh
```

### 2. Neuen Server überprüfen

Prüfen Sie die Administrationsoberfläche unter `https://ihr.neuer.hostname/admin/` und bestätigen Sie, dass Migrationen angewendet wurden:

```bash
ophix-manage migrate --check
```

### 3. Import-Befehl ausführen

```bash
ophix-manage import_legacy_credserver \
    --db-host <alter-db-host> \
    --db-name <alter-db-name> \
    --db-user <alter-db-user> \
    --db-password <alter-db-passwort>
```

Verwenden Sie zuerst `--dry-run`:

```bash
ophix-manage import_legacy_credserver --db-name credserver_db --dry-run
```

Für eine PostgreSQL-Quelldatenbank:

```bash
ophix-manage import_legacy_credserver --db-engine postgres --db-name ...
```

### 4. Importierte Daten überprüfen

Melden Sie sich in der neuen Administrationsoberfläche an und prüfen Sie:

- Alle Hosts erscheinen unter **Clients & Hosts → Hosts**
- Alle Clients erscheinen unter **Clients & Hosts → Clients**
- Alle Anmeldeinformationen erscheinen unter **Anmeldeinformationen**
- Client-Anmeldeinformationen-Verknüpfungen sind intakt

### 5. Client-Konfiguration aktualisieren

```bash
cred-client set server https://neuer.credserver.hostname
cred-client download ca-cert   # falls das TLS-CA geändert wurde
```

### 6. Alten Server stilllegen

Sobald alle Clients am neuen Server verifiziert sind, alten Server stoppen und entfernen.

---

## Hinweise

- **Tokens werden beibehalten.** Die `api_token`-Werte werden unverändert übernommen — Clients verbinden sich ohne Neuregistrierung.
- **Verschlüsselung.** Der `CRED_ENCRYPTION_KEY` auf dem neuen Server ist unabhängig vom alten Server. Sichern Sie diesen Schlüssel separat.
- **Neue Berechtigungsspalten.** `can_update`, `can_delete` und `can_share` sind beim Import alle `False`. Überprüfen Sie diese in der Administrationsoberfläche, falls client-seitige Schreibzugriffe benötigt werden.
- **Die alte Datenbank wird während des Imports nie verändert.**
