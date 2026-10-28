# DWD-Niederschlagsvorhersage – deutscher Fork

Privater Fork von [stoppegp/ha-dwd-precipitation-forecast](https://github.com/stoppegp/ha-dwd-precipitation-forecast) für Home Assistant. Deutschsprachige Fassung mit zusätzlicher Erkennung der aktuellen Niederschlagsart.

**Unabhängiges Projekt, keine offizielle Integration des Deutschen Wetterdienstes.**

## Aktueller Stand

Die vorhandene Integration liefert für einen Standort innerhalb des deutschen DWD-Radargebiets:

- aktuelle Niederschlagsintensität in mm/h;
- eine radarbasierte Vorhersage für die nächsten zwei Stunden in Fünfminutenschritten;
- Beginn, Ende, Dauer und Intensität des nächsten vorhergesagten Niederschlagsereignisses;
- Hinweise auf Niederschlag innerhalb der nächsten 15, 30 und 60 Minuten.

Die Integration ruft die RV-Radardaten alle fünf Minuten ab. Datenbereitstellung und Übertragung können zu zeitlichem Versatz führen. Die Daten sind räumliche Radarschätzungen und keine Messung unmittelbar am Haus.

Ab Version **1.0.0** sind Einrichtung, Standardnamen und neue Zustände deutschsprachig. Der Fork verwendet eine eigene Integrationskennung und eigene Entitäten. Die bisherige Integration wird nicht ersetzt. RV liefert Niederschlagsmengen; die aktuelle Niederschlagsart kommt separat aus HymecNG.

## Aktuelle Niederschlagsart (HymecNG)

Der zusätzliche Sensor **Niederschlagsart** liest das DWD-Produkt **HymecNG** alle fünf Minuten aus. Er unterscheidet keinen Niederschlag, nicht klassifizierbaren Niederschlag, Sprühregen, Regen, gefrierenden Sprühregen, gefrierenden Regen, Schneeregen, Schnee, Graupel, Hagel und großen Hagel. Das Symbol passt sich der Art an.

Der Sensor enthält den Datenstand, den normalisierten Klassencode und die Kennzeichnung `ist_vorhersage: false`. Die Auflösung beträgt 1 × 1 km. Fehlende Daten, Abruffehler und ein mehr als 20 Minuten alter Datenstand werden als nicht verfügbar behandelt. Nicht klassifizierbarer Niederschlag bleibt als solcher erkennbar. Die RV-Vorhersage und HymecNG werden unabhängig abgerufen: Ein HymecNG-Ausfall schaltet die RV-Sensoren nicht ab.

**HymecNG beschreibt die aktuelle Niederschlagsart, nicht die Art zukünftigen Niederschlags.** Ein Schneewert darf deshalb nicht pauschal auf die nächsten zwei Stunden übertragen werden. Die vorhandene Dashboard-Karte wird durch ein Integrationsupdate nicht automatisch geändert.

## Installation zum privaten Test

Der Fork wird nicht im HACS-Standardkatalog oder einem Marketplace veröffentlicht. Eine optionale Installation als benutzerdefiniertes HACS-Repository ist davon unabhängig.

### Vorhandene Installation

Der Fork verwendet den eigenen technischen Integrationsnamen `dwd_forecast_german` und den eigenen Ordner `custom_components/dwd_forecast_german`. Original und Fork können parallel installiert werden. Der Originalordner `custom_components/dwd_precipitation_forecast` bleibt unverändert. Den Standort für den Fork separat über die Oberfläche einrichten; vorhandene Karten und Automationen wechseln nicht automatisch auf die neuen Entitäten.

### Manuelle Installation

1. Den gewünschten Stand dieses Repositorys als ZIP herunterladen.
2. Den Ordner `custom_components/dwd_forecast_german` in den Ordner `custom_components` der Home-Assistant-Konfiguration kopieren.
3. Home Assistant neu starten.
4. Falls noch nicht eingerichtet: unter „Einstellungen → Geräte & Dienste“ die Integration „DWD Niederschlagsvorhersage“ hinzufügen und Standortname, Breitengrad und Längengrad eingeben.

### Optional über HACS

Dieses Repository als benutzerdefiniertes Repository vom Typ „Integration“ hinzufügen:

`https://github.com/soundclub83/ha_dwd_forecast_german`

## Dashboard-Beispiel

Die Bilder stammen aus dem ursprünglichen Projekt. Das folgende Beispiel verwendet neutrale Niederschlagstexte, weil RV keine Niederschlagsart liefert.

![Niederschlagsvorhersage aus dem ursprünglichen Projekt](precipitation_forecast_card.png)
![Weiteres Beispiel aus dem ursprünglichen Projekt](precipitation_forecast_card2.png)

Benötigte Komponenten:

- [Mushroom Template Card](https://github.com/piitaya/lovelace-mushroom)
- [easy-time-jinja](https://github.com/Petro31/easy-time-jinja)
- [card-mod](https://github.com/thomasloven/lovelace-card-mod)

Die Entität `sensor.dwd_forecast_german_leipzig` im Beispiel an beiden Stellen durch den eigenen Sensor ersetzen.

```yaml
type: custom:mushroom-template-card
primary: >-
  {% from 'easy_time.jinja' import custom_time, custom_relative_time, custom_time_between %}
  {% if not is_state_attr(entity, 'next_start', 'unknown') %}
    {% set next_start = state_attr(entity, 'next_start') %}
    {% set next_end = state_attr(entity, 'next_end') %}
    {% if next_start is not none and next_end is not none %}
      {% if next_start | as_timestamp > now() | as_timestamp %}
        In {{ custom_time(next_start, 'hour, minute', 'de') }} wird Niederschlag für {{ state_attr(entity, 'next_length') }} Minuten erwartet.
      {% elif next_end is not none %}
        Niederschlag dauert noch {{ custom_time_between(now() | as_timestamp, next_end | as_timestamp, 'hour, minute', None, None, 'de') }}.
      {% else %}
        Niederschlag dauert noch mindestens 2 Stunden an.
      {% endif %}
    {% elif next_start is not none %}
      {% if next_start | as_timestamp > now() | as_timestamp %}
        In {{ custom_time(next_start, 'hour, minute', 'de') }} beginnt Niederschlag.
      {% else %}
        Niederschlag dauert noch mindestens 2 Stunden an.
      {% endif %}
    {% else %}
      Kein Niederschlag in den nächsten 2 Stunden.
    {% endif %}
  {% else %}
    Kein Niederschlag in den nächsten 2 Stunden.
  {% endif %}
icon: mdi:weather-rainy
icon_color: |-
  {% if float(states(entity)) > 0 %}
  blue
  {% else %}
  grey
  {% endif %}
entity: sensor.dwd_forecast_german_leipzig
card_mod:
  style: |
    {% set entity = 'sensor.dwd_forecast_german_leipzig' %}
    ha-card {
      background-image: linear-gradient(90deg{% set entity = entity %}{% set duration = state_attr(entity, 'forecast').keys() | last | as_timestamp - now() | as_timestamp %}{% set hue_min = 200 %}{% set hue_max = 300 %}{% set prec_max = 20 %}{% for x, y in state_attr(entity, 'forecast').items() %}{% set pos = ((x | as_timestamp - (now() | as_timestamp))/duration*100) | round %}{% set hsl_h = (y/prec_max*(hue_max-hue_min)+hue_min)|round %}{% set hsl_l = 50 if y > 0 else 100 %}{% set hsl_alpha = 0.5 if y > 0 else 0 %}{% if pos >= -4 %}, hsla({{hsl_h}}, 100%, {{hsl_l}}%, {{hsl_alpha}}) {{ max(pos,0) }}%{% endif %}{% endfor %});
    }
```

## Technische Änderungen in 1.0.0

- DWD-HDF5-Projektion statt der alten sphärischen Standortformel; dadurch kann die gewählte Rasterzelle gegenüber dem Original abweichen.
- Skalierung und Offset aus dem RV-Dateiheader; fehlende Werte werden nicht als Niederschlag ausgegeben.
- Prüfung vollständiger RV-Zeitreihen und veralteter Daten; HTTP-Zeitlimits.
- Zusätzliche Abhängigkeit `pyproj` zur Koordinatenumrechnung. Die erforderlichen Pakete werden von Home Assistant installiert; ein Neustart ist nach dem Austausch notwendig.
- Die Struktur der Prognoseattribute und die Zustände der 15-/30-/60-Minuten-Sensoren entsprechen dem Original. Wegen der getrennten Integration müssen Karten und Automationen für den Fork ausdrücklich auf dessen neue Entitäten eingestellt werden.

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
