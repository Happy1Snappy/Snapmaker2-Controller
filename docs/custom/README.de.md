# Persönliche A350-Laser-Firmware

**Sicherheitsfehler LA01:** Bei nativer Marlin-Inline-Steuerung kann nach
Pause/Stop die letzte Laserleistung am stehenden Kopf erhalten bleiben.
Gemeldet mit 10 W und LightBurn 2.2.1. LA01 bis zur Korrektur nicht für
Laserjobs verwenden. Ein erfolgreicher Build ersetzt keinen Hardwaretest.

## Basis und Status

- Basis: offizieller Tag `v5.2.1`, Commit
  `314c167b0a1ce331d867b10abd32e00908e4aa9c`.
- Experimentelle Controller-Version: `SM2-5.2.1-LA01`.
- Touchscreen, Controller und Module haben eigene Firmwareversionen.
  Die Touchscreen-Version 2.4 ist nicht die Controller-Version 5.2.1.
- Ziel: ursprünglicher A350 mit fünf 8-mm-Spindeln, Originalnetzteil,
  Quick Swap, Gehäuse und Türerkennung; LightBurn direkt über USB.
- Windows-Build, Paketierung und erste Maschinentests vom Besitzer bestätigt.
- Inoffizieller persönlicher Fork; keine allgemeine Kompatibilitätszusage.

## LightBurn: native Marlin-Profile verwenden

Diese Custom-Version wird mit **nativen Marlin-Geräteprofilen** direkt über
USB betrieben. SnapMaker-Geräteprofile werden für diesen Arbeitsstand nicht
verwendet. Der Besitzer berichtet funktionierendes Streaming und Framing mit
Marlin-Profilen sowie grundsätzlich funktionierende weitere Bedienung.

**Im Inline-Modus muss die Leistung für Framing und Fokuspunkt im
LightBurn-Profil höher eingestellt werden, damit die Ausgabe sichtbar wird.**
Ein allgemeingültiger Prozentwert wurde nicht ermittelt; die Einstellung
bleibt abhängig vom Laserkopf und Profil. Nur so weit erhöhen, wie für die
Sichtbarkeit erforderlich. Framing-Leistung und Kreuzlaser-Versatz bleiben
auf Profilebene, nicht als feste Werte im Firmwarecode.

Der Besitzer hat auch den **ersten Test des 2-W-IR-Kopfs mit einem nativen
Marlin-Profil abgeschlossen**. Weitere intensive Tests folgen. Einzelne
Funktionen wie Kreuzlaser-Framing, Pause und Abbruch wurden in dieser
Rückmeldung nicht separat beschrieben und gelten deshalb noch nicht als
einzeln dokumentiert abgenommen. Die allgemeine Rückmeldung ersetzt keine
getrennte Abnahme aller Funktionen an jedem Kopf.

Die SnapMaker-Profile starteten auch nach dem unten beschriebenen Wechsel
der Touchscreen-Firmware keinen Stream. Die Ursache ist nicht abschließend
geklärt; ein LightBurn-Problem ist eine Vermutung des Besitzers. Die weitere
Untersuchung dieser Profile ist vorerst eingestellt.

## Gemeldeter Testaufbau

Der Besitzer installierte zunächst das vollständige offizielle V1.21-Paket
(Touchscreen und Controller; danach Controller V4.7.x) und anschließend das
Controller-Paket `5.2.1-LA01`. Für diesen Aufbau wurden die aktuellen Ergebnisse
gemeldet. Die genaue verbleibende Touchscreen- und die einzelnen Modulversionen
wurden noch nicht protokolliert. Diese Abfolge ist eine Beschreibung des
Testaufbaus, keine erforderliche Installations- oder Downgrade-Anleitung.

## Änderungen LA01

`M7` und `M8` schalten die Originalpumpe ein, `M9` schaltet sie aus.
Die vorhandene Bewegungssynchronisierung vor dem Umschalten bleibt bestehen.
Die gemeinsame Freigabe in G-Code und Ausgangs-ISR umfasst nun 1,6 W,
10 W, 20 W und 40 W. 2 W IR wird nicht zusätzlich freigegeben.

Die Pumpe wird über den Heizbett-Ausgang geschaltet, nicht über einen
CAN-Befehl an die Pumpe. Die tatsächliche Kopf-ID bleibt unverändert.
Beim Initialisieren wird der Pumpenwunsch zurückgesetzt. Beim Wiederanlauf
werden die gespeicherten Pumpenzustände auch für 1,6 W und 10 W übernommen,
ohne Kreuzlaser-CAN-Befehle an diese Köpfe zu senden.
Die vorhandenen Stop- und Quick-Stop-Pfade setzen den Pumpenzustand für beide
Köpfe bereits zurück; Quick Stop umfasst auch Pause und Schutzereignisse.
Die tatsächliche Reaktionszeit und der USB-Abbruchpfad sind am Gerät zu prüfen.

**Bei Laserbetrieb darf am Heizbett-Anschluss ausschließlich die dafür
vorgesehene Pumpenansteuerung hängen, kein Heizbett.** Die Firmware enthält
weiterhin die anderen Betriebsarten; sie wurden nicht ausgebaut.

Framing-Leistung und Kreuzlaser-Versatz bleiben in den LightBurn-Profilen.
Inline-Verhalten, Achsgrenzen, Beschleunigung, Türerkennung und Touchscreen-
Bedienung werden durch diesen Patch nicht absichtlich geändert. Ihre
Funktion muss am Gerät geprüft werden.

## Build-Prüfung

Original und Custom-Version wurden unter Linux erfolgreich kompiliert.
Paketierung und Paketinhalt wurden geprüft. Details: [BUILD-REPORT.md](BUILD-REPORT.md).
Ein Fehler der ursprünglichen Paketierung wurde korrigiert: Datum und `.bin`
des Controller-Dateinamens dürfen nicht Teil der Versionsnummer werden.

## Windows 11 / VS Code / PlatformIO

1. Git, VS Code und die PlatformIO-IDE-Erweiterung installieren.
2. Repository klonen und Branch auswählen:

   ```powershell
   git clone https://github.com/Happy1Snappy/Snapmaker2-Controller.git
   cd Snapmaker2-Controller
   git switch laser-custom
   ```

3. Den gesamten Repository-Ordner in VS Code öffnen. In einem PlatformIO-
   Terminal bauen:

   ```powershell
   pio run -e GD32F105
   pio run -e GD32F105 -t pack
   ```

Geprüfte Build-Werkzeuge hier unter Linux (Windows-Build vom Besitzer bestätigt):
PlatformIO Core 6.2.0, ststm32 20.0.0, GCC-ARM-Paket 1.70201.0,
Maple-Framework 3.10000.201129. Plattform, Compiler und Framework sind
in `platformio.ini` für `GD32F105` festgeschrieben.

Das Rohimage liegt in `.pioenvs/GD32F105/firmware.bin`, das verpackte
Update im Ordner `release/`. `pack` muss nach einem erfolgreichen Build
aufgerufen werden. PlatformIO-Upload ist hier ein Debug-Probe-Upload und
kein LightBurn-USB-Update; nicht als Installationsweg verwenden.

Für spätere Änderungen `SHORT_BUILD_VERSION` in `Marlin/src/inc/Version.h`
eindeutig erhöhen, da Snapmaker identische Versionen eventuell nicht lädt.

## Installation und Rückkehr

Vor einem Hardwaretest die bisherige offizielle Update-Datei separat sichern,
Maschineneinstellungen dokumentieren und den offiziellen USB-Updateweg prüfen.
Ein Firmwarepaket enthält hier nur den Controller; Touchscreen und Werkzeugköpfe
werden damit nicht auf eine zu diesem Quellstand passende Version gebracht.
Kompatibilität mit den installierten Modulversionen ist noch zu prüfen.

Build und Paket wurden geprüft; erste Hardwaretests sind erfolgt. Für andere
Konfigurationen ist die Kompatibilität nicht nachgewiesen. Eine Rückkehr
benötigt ein zur jeweiligen Maschine passendes offizielles Updatepaket. Ein Repository zu löschen setzt keine Maschine
zurück und entfernt keine bereits angefertigten Kopien.

## Weitere Hardware-Abnahme

- Nach Einschalten Pumpe und Bearbeitungslaser aus.
- Mit 10 W und 1,6 W: jeweils `M7`, `M9`, `M8`, `M9` über die USB-Konsole
  prüfen; diese Befehle enthalten keine Laser-Einschaltanweisung.
- Mit 40 W: bisheriges Pumpenverhalten unverändert prüfen.
- Wechsel zwischen Air-Assist-Layern: Umschalten erst nach den vorherigen
  Bewegungen, danach korrekter Pumpenzustand.
- Jobende mit `M9`, Abbruch, Pause/Wiederanlauf und Türöffnung prüfen.
  Ein bloßes USB-Verbindungsende ist kein nachgewiesener Stop-Befehl.
- Verhalten bei USB-Verlust separat erfassen; kein automatisches Abschalten
  behaupten, bevor es am tatsächlichen Streaming-Pfad nachgewiesen wurde.
- Touchscreen: Achsen, Origin und Go to Work prüfen.
- Später: Framing 1,6/10 W mit reduzierter Leistung, Kreuzlaser 40 W/IR,
  Inline-Leistung, Leerfahrten und Abbruch mit LightBurn-Profilen testen.

Aktueller Arbeitsweg: LightBurn mit nativen Marlin-Profilen. Kein Wechsel
zu SnapMaker-Profilen vorgesehen. Die genaue getestete LightBurn-Version
und die endgültigen Profilwerte sollten zusammen mit den Kopf-Tests
protokolliert werden.
