# DWD-Niederschlagsvorhersage – deutscher Fork

Privater Fork von [stoppegp/ha-dwd-precipitation-forecast](https://github.com/stoppegp/ha-dwd-precipitation-forecast) für Home Assistant. Ziel ist eine deutschsprachige Fassung mit ergänzender Erkennung der aktuellen Niederschlagsart.

**Unabhängiges Projekt, keine offizielle Integration des Deutschen Wetterdienstes.**

## Aktueller Stand

Die vorhandene Integration liefert für einen Standort innerhalb des deutschen DWD-Radargebiets:

- aktuelle Niederschlagsintensität in mm/h;
- eine radarbasierte Vorhersage für die nächsten zwei Stunden in Fünfminutenschritten;
- Beginn, Ende, Dauer und Intensität des nächsten vorhergesagten Niederschlagsereignisses;
- Hinweise auf Niederschlag innerhalb der nächsten 15, 30 und 60 Minuten.

Die Integration ruft die RV-Radardaten alle fünf Minuten ab. Datenbereitstellung und Übertragung können zu zeitlichem Versatz führen. Die Daten sind räumliche Radarschätzungen und keine Messung unmittelbar am Haus.

**Dieser erste Änderungsstand überarbeitet nur Dokumentation und Lizenzhinweise.** Die Einrichtung und Sensornamen sind noch nicht vollständig eingedeutscht. RV liefert Niederschlagsmengen, keine Unterscheidung zwischen Regen, Schnee und Schneeregen.

## Geplante Erweiterung

Die aktuelle Niederschlagsart soll zusätzlich aus dem DWD-Produkt **HymecNG** ausgelesen werden, beispielsweise Regen, Schnee, Schneeregen, gefrierender Regen oder Hagel. Diese Erweiterung ist noch nicht implementiert. HymecNG beschreibt die aktuelle Niederschlagsart; daraus allein ergibt sich keine Vorhersage der Niederschlagsart für die nächsten zwei Stunden.

Installationshinweise, Dashboard-Beispiel und Lizenzhinweise stehen in der [README](https://github.com/soundclub83/ha_dwd_forecast_german/blob/main/README.md).

## Herkunft und Lizenzen

### Software

Dieser Fork basiert auf [ha-dwd-precipitation-forecast von stoppegp](https://github.com/stoppegp/ha-dwd-precipitation-forecast), Ausgangsstand `fd446595ba956f5d744ca5a3a96d0a5129e5c595`.

Der ursprüngliche Code steht unter der **MIT-Lizenz**, Copyright © 2024 stoppegp. Die ursprüngliche Lizenz und der Copyright-Vermerk bleiben in [LICENSE](LICENSE) erhalten. Eigene Änderungen dieses Forks stehen ebenfalls unter MIT. Die Lizenz erlaubt Nutzung, Änderungen und Weitergabe unter Beibehaltung der Lizenz- und Copyright-Hinweise; sie enthält einen Gewährleistungs- und Haftungsausschluss.

### Wetterdaten

Die Softwarelizenz gilt nicht für die bezogenen Wetterdaten. Datenquelle ist der **Deutsche Wetterdienst (DWD)**. Für die offenen DWD-Geodaten gelten die jeweiligen DWD-Nutzungsbedingungen und **Creative Commons Namensnennung 4.0 International (CC BY 4.0)**.

- [DWD Open Data](https://opendata.dwd.de/)
- [Nutzungsbedingungen laut DWD-Open-Data-Server](https://www.dwd.de/EN/service/legal_notice/legal_notice_node.html)
- [DWD-Erklärung zur Weiterverwendung offener Geodaten](https://www.naturgefahrenportal.de/de/copyright)
- [CC BY 4.0 – vollständiger Lizenztext](https://creativecommons.org/licenses/by/4.0/legalcode.de)

Bei Weitergabe oder öffentlicher Darstellung der verarbeiteten Daten sind Datenquelle und Lizenz anzugeben und Änderungen kenntlich zu machen. Beispiel für durch diesen Fork verarbeitete Daten:

> Datenquelle: Deutscher Wetterdienst (DWD), CC BY 4.0. Für Home Assistant aufbereitet durch ha_dwd_forecast_german; Werte für den gewählten Standort aus dem DWD-Raster extrahiert und in mm/h umgerechnet.

Originaldaten, Datenstand und eigene Verarbeitung sollen unterscheidbar bleiben. Aus den Daten abgeleitete Anzeigen sind keine amtlichen Wetterwarnungen. Dieser Fork ist ein unabhängiges privates Projekt und wird weder vom DWD herausgegeben noch unterstützt. Die Nutzung der Daten räumt keine Rechte an DWD-Logos oder anderen geschützten Kennzeichen ein.
