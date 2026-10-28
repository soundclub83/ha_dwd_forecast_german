# Änderungen

## 1.0.1

- Importfehler bei der Einrichtung unter Home Assistant 2026.10 behoben: Beide Sensoren beziehen den Quellenhinweis aus einer gemeinsamen Textkonstante. Es wird keine von Home Assistant umgewandelte `_attr_attribution`-Eigenschaft aus einer anderen Sensorklasse übernommen.
- Der Test für die HA-Anbindung bildet diese Descriptor-Regel nun nach. Mit dem fehlerhaften Code reproduziert er den gemeldeten Importfehler; mit der Korrektur bestehen alle 29 Tests.
- Keine Änderung an Standortkonfiguration, Niederschlagsdaten oder Entitätskennungen.

## 1.0.0

- Eigene Integrationskennung `dwd_forecast_german` für die parallele Installation zum Original.
- Deutschsprachige Einrichtung, Sensorbezeichnungen und Niederschlagsarten.
- Zusätzlicher HymecNG-Sensor für die aktuelle Niederschlagsart.
- Getrennte Abrufe für RV und HymecNG sowie Prüfung von Datenstand und fehlenden Rasterwerten.
