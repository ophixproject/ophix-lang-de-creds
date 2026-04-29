---
title: Anmeldeinformationen
slug: credentials
order: 100
section: Anmeldeinformationen
---

Die Anmeldeinformationen-Domäne speichert benannte JSON-Geheimnisse und verteilt sie über HTTPS an autorisierte Clients. Geheimnisse werden bei Bedarf abgerufen und ausschließlich im Arbeitsspeicher verwendet — sie werden clientseitig nie auf die Festplatte geschrieben.

Jede Anmeldeinformation ist ein benanntes Objekt, das beliebiges JSON enthält (`secret_json`). Der Zugriff wird pro Client kontrolliert: Ein Client kann nur die Anmeldeinformationen abrufen, mit denen er von einem Administrator explizit verknüpft wurde.

---

## Verschlüsselung im Ruhezustand

Das Feld `secret_json` wird im Ruhezustand in der Datenbank mit Fernet-Symmetricverschlüsselung (AES-128-CBC mit HMAC-SHA256) verschlüsselt. In der Datenbankspalte wird das verschlüsselte Token gespeichert — das Geheimnis im Klartext wird nie in lesbarer Form auf die Festplatte geschrieben.

Verschlüsselung und Entschlüsselung laufen transparent ab: Die Administrationsoberfläche, die API und Client-Tools arbeiten alle mit dem JSON-Klartextwert.

### Ersteinrichtung

Bevor Sie `migrate` zum ersten Mal ausführen, generieren Sie einen Verschlüsselungsschlüssel:

```bash
ophix-manage generate_cred_key
```

Dieser Befehl gibt einen Schlüssel aus. Fügen Sie ihn Ihrer `.env` hinzu:

```ini
CRED_ENCRYPTION_KEY=<generierter Schlüssel>
```

Dann führen Sie die Migrationen aus:

```bash
ophix-manage migrate
```

Die Migration verschlüsselt alle vorhandenen Klartextdatensätze. Wenn `CRED_ENCRYPTION_KEY` nicht gesetzt ist, stoppt die Migration mit einer klaren Fehlermeldung, bevor Änderungen vorgenommen werden.

### Schlüsselverwaltung

- Der Schlüssel ist ein 32-Byte-Fernet-Schlüssel, der als URL-safe Base64 in `.env` gespeichert ist
- **Erstellen Sie ein separates Backup des Schlüssels von der Datenbank.** Der Verlust des Schlüssels bedeutet den Verlust des Zugriffs auf alle gespeicherten Anmeldeinformationen

### Schlüsselrotation

Um den Verschlüsselungsschlüssel zu ersetzen und alle Anmeldeinformationen neu zu verschlüsseln:

```bash
ophix-manage rotate_cred_key
```

Verwenden Sie `--no-input` für geplante/automatische Rotation.

---

## cred-client

`cred-client` ist der Tier-1-Kommandozeilen-Client für den Ophix-Anmeldeinformationsserver. Die Konfiguration wird in `.cred.env` gespeichert.

| Variable | Beschreibung |
| --- | --- |
| `CREDSERVER_URL` | Basis-URL des Anmeldeinformationsservers |
| `CREDSERVER_CA_CERT` | Pfad zum CA-Zertifikat des Servers |
| `CREDSERVER_API_TOKEN` | 64-stelliges hexadezimales API-Token |

### Installation

```bash
pip install ophix-cred-client
```

### Initialisierung

```bash
# Ein Schritt
cred-client quickstart https://credserver.internal mein-client

# Schritt für Schritt
cred-client set server https://credserver.internal
cred-client download ca-cert
cred-client register mein-client
```

### Token-Rotation

```bash
cred-client rotate-token
```

Validiert das neue Token, bevor `.cred.env` überschrieben wird. Kann aus Cron ausgeführt werden.

### Anmeldeinformationen abrufen

```bash
cred-client fetch db_prod         # gibt JSON auf stdout aus
```

### Überprüfung

```bash
cred-client check --all                    # alle zugeordneten Anmeldeinformationen prüfen
cred-client check --all --verbose          # Fehlerdetails anzeigen
cred-client check --var DB_PROD_CRED_NAME  # nach Umgebungsvariable prüfen
cred-client check --name db_prod           # nach Name prüfen
```

---

## Anmeldeinformationen in der Administration verwalten

Anmeldeinformationen und Client-Zugriffe werden über die Django-Administration verwaltet:

- **Anmeldeinformationen** — Anmeldeinformationen erstellen und bearbeiten, Clients mit Zugriff anzeigen
- **Client**-Detailseite — über die Inline-Ansicht verwaltete Anmeldeinformationen eines Clients bearbeiten

Wenn Sie einen Client mit einer Anmeldeinformation verknüpfen, steuert das Kontrollkästchen **enabled** auf dem Link, ob der Zugriff aktiv ist. Deaktivierte Links werden in der Administrationsliste kursiv und gedämpft angezeigt.

---

## API-Referenz

Alle Anfragen erfordern `Authorization: Token <api_token>` und müssen von der registrierten Host-IP stammen.

### Anmeldeinformation abrufen

```http
GET /api/credentials/<name>/
```

### Anmeldeinformation erstellen

```http
POST /api/credentials/<name>/
Content-Type: application/json

{
  "secret_json": { "KEY": "Wert" },
  "description": "Optionale Beschreibung"
}
```

### Anmeldeinformation aktualisieren

```http
PUT /api/credentials/<name>/
```

Erfordert `can_update` auf dem Client-Anmeldeinformation-Link.

### Anmeldeinformation löschen

```http
DELETE /api/credentials/<name>/
```

Erfordert `can_delete` auf dem Link **und** `ENABLE_ARTIFACT_DELETE=true` in `.env`.

---

## Servereinstellungen

| Variable | Standard | Beschreibung |
| --- | --- | --- |
| `CRED_ENCRYPTION_KEY` | _(erforderlich)_ | Fernet-Verschlüsselungsschlüssel. Mit `ophix-manage generate_cred_key` generieren. |
| `ENABLE_ARTIFACT_DELETE` | `False` | Clients erlauben, eigene Anmeldeinformationen zu löschen. |
| `AUTH_LEAK_INFO` | `False` | Fehlerdetails in API-Antworten aufnehmen. Nur in der Entwicklung auf `True` setzen. |
| `MINIMUM_TOKEN_ROTATE_TIME` | `3600` | Mindestintervall zwischen Token-Rotationen in Sekunden. |

---

## Zugriffskontrolle

Jede Anfrage wird durch vier Schichten validiert:

1. `Host.enabled` — der Host-Rechner ist registriert und aktiv
2. `Client.enabled` — der spezifische Client-Prozess ist aktiv
3. `Credential.enabled` — die Anmeldeinformation selbst ist aktiv
4. `ClientCredential.enabled` — dieser Client hat Zugriff auf diese Anmeldeinformation erhalten

Wenn eine Schicht fehlschlägt, gibt die Anfrage **403 Forbidden** zurück.
