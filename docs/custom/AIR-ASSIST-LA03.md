# LA03: Air Assist bei Inline-Pause und Fortsetzen

Controller-Version `SM2-5.2.1-LA03`, Branch `laser-inline-stop`.
Aufbauend auf LA02, dessen Laserabschaltung der Besitzer als funktionierend
zurückgemeldet hat. Die neue Pumpenfunktion ist noch nicht am Gerät getestet.

## Verhalten

- M7/M8 fordern Air Assist an, M9 löscht die Anforderung.
- Nach Ende der letzten Inline-Bewegung ohne ausführbare Folgebewegung wird
  zusätzlich zur Laser-PWM auch die Pumpenausgabe vorübergehend gesperrt.
- Der angeforderte Ebenenzustand bleibt erhalten. Die nächste Inline-Bewegung
  hebt die Sperre auf: Pumpe wieder an, sofern die Ebene Air Assist anfordert.
  Das gilt auch für Inline-Blöcke mit Leistung null, etwa Raster-Leersegmente.
- M9 während der Pause verhindert das Wiederanlaufen. Ein ausdrückliches
  M7/M8 kann die Pumpe wie bisher manuell einschalten.
- Ein ausdrücklicher Planner Quick Stop (u.a. M410) sowie kill/M112 löschen
  die Pumpenanforderung. Sie wird danach nur durch eine neue Anforderung,
  etwa M7/M8, wieder aktiv. Die vorhandenen Snapmaker-Pause-/Resume-Pfade
  speichern und restaurieren ihren Ebenenzustand weiterhin separat.

Die Temperatur-ISR steuert den Heizbett-Ausgang jetzt anhand von Anforderung
UND fehlender Sperre. Der gespeicherte Wiederanlaufzustand verwendet weiterhin
nur die Anforderung. Kein CAN-Befehl an die Pumpe, keine Bewegung als Umweg.
Keine neue Air-Assist-Freigabe für den 2-W-IR-Kopf.

## Grenzen

Wie bei LA02 ist ohne Host-Signal nicht erkennbar, ob eine Datenlücke Pause,
Stop oder eine vorübergehende Streaming-Unterbrechung bedeutet. Bei einem
bloßen Auslaufen des Puffers bleibt die Anforderung erhalten; eine spätere
Inline-Bewegung (auch eine manuell veranlasste) gibt sie wieder frei. Für ein
sicheres Löschen der Anforderung M9 verwenden. Ob der LightBurn-Stop-Knopf
zusätzlich einen ausdrücklichen Stop sendet, ist noch nicht aufgezeichnet.

Daher kann die Pumpe auch bei echten Pufferunterläufen aus- und einschalten.
Direkt folgende Inline-Blöcke lösen keine zusätzliche Pumpenpause aus.
Die Ausgabe folgt der nächsten Temperatur-ISR; mechanischer Nachlauf der
Pumpe ist möglich. Beim Wiederanlauf ist keine zusätzliche Druckaufbauzeit
vor dem Laserstart implementiert. Das muss beim Materialtest berücksichtigt
werden. Die weiteren Grenzen von [LA02](INLINE-STOP-LA02.md) gelten weiterhin.

## Prüfung und nächster Test

Firmware-Build und Host-Regressionstests bestanden. Der Test führt die echten
Getter, SetAirPumpSwitch, BlankOutput_ISR, TurnOn_ISR und Quick-Stop-Helfer
gegen simulierte Hardware aus. Geprüft: Pause behält Anforderung bei Ausgabe
aus; Fortsetzen schaltet wieder ein; M9 verhindert Wiederanlauf; expliziter
Stop löscht die Anforderung; manuelles M7 bleibt möglich. Die bisherigen
Laser-Abschalt-, Fokus- und Pakettests bestehen ebenfalls.

Zuerst einen Bewegungsjob mit Laserleistung null und Air Assist an testen:
Pause, Auslaufen der Bewegungen, Pumpe aus, Fortsetzen, Pumpe an. Danach
mit Air Assist aus wiederholen; die Pumpe muss aus bleiben. Zusätzlich M9
während einer Pause und Stop getrennt prüfen. Keine Bearbeitungsleistung
für diese Pumpentests erforderlich. Vollständige Hardwareabnahme ausstehend.

## Build-Artefakt

Linux-Build: RAM 82.712 / 98.304 Bytes, Flash 297.992 / 524.288 Bytes.
Paketierung, Paketkopf, Prüfsumme und eingebettetes Rohimage geprüft.
Lokales Paket `Snapmaker_V5.2.1-LA03_20261120.bin`:
300088 Bytes, SHA-256 `a90394109623c8b5740781535a236fc268c7722f71d7fc0f6ab7d35f0e42d602`. Kein Binärrelease veröffentlicht.
