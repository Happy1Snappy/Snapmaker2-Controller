# Persönliche A350-Laser-Firmware

## Basis und Status

- Basis: offizieller Tag `v5.2.1`, Commit
  `314c167b0a1ce331d867b10abd32e00908e4aa9c`.
- Experimentelle Controller-Version: `SM2-5.2.1-LA01`.
- Die installierte Paketversion `Snapmaker_V2.4.0_20251231` ist keine
  Versionsnummer dieses Controller-Quellstands. Eine identische Zuordnung
  der beiden Versionen wurde nicht nachgewiesen.
- Ziel: ursprünglicher A350 mit fünf 8-mm-Spindeln, Originalnetzteil,
  Quick Swap, Gehäuse und Türerkennung; LightBurn direkt über USB.
- Kein Hardwaretest durchgeführt. Windows-Build noch nicht geprüft.
- Inoffizieller persönlicher Fork; keine allgemeine Kompatibilitätszusage.

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

Geprüfte Build-Werkzeuge (Linux; Windows-Prüfung ausstehend):
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

Noch keine Installationsempfehlung: Erst Build und Paket prüfen, dann mit
kontrolliertem Aufbau testen. Eine Rückkehr erfolgt grundsätzlich über ein
passendes offizielles Updatepaket; ob die installierte Beta einen Downgrade
akzeptiert, ist vorab zu klären. Ein Repository zu löschen setzt keine Maschine
zurück und entfernt keine bereits angefertigten Kopien.

## Hardware-Abnahme (noch offen)

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

LightBurn 2.2.x ist das Ziel. Alte Profile/1.4.5 bleiben Vergleichsmaterial.
Noch keine Aussage, dass LA01 den bisherigen Profilwechsel ersetzt.
