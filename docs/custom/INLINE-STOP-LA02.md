# LA02: Inline-Ausgang nach Bewegungsende und Abbruch

**Experimenteller Korrekturstand, noch nicht am Gerät abgenommen.**
Branch: `laser-inline-stop`; Controller-Version: `SM2-5.2.1-LA02`.
LA01 enthält den unten beschriebenen Sicherheitsfehler und soll nicht weiter
für Laserjobs verwendet werden. Ein erfolgreicher Build ist keine Freigabe
für Laserbetrieb.

## Befund

Vom Besitzer gemeldet: 10-W-Kopf, LightBurn 2.2.1, natives Marlin-Profil,
Inline-Steuerung. Bei Pause/Stop endet die Bewegung, die Laserquelle bleibt
aktiv. Eine anschließende manuelle Bewegung schaltet sie ab. Ob LightBurn
beim Klick einen Stop-Befehl sendet oder nur die Datenübertragung anhält,
ist ohne Aufzeichnung noch nicht bekannt.

Im ursprünglichen Stepper-Pfad wird die Inline-PWM beim Start und während
der Bewegung ausgegeben, nach dem letzten Block ohne Folgebewegung aber
nicht ausdrücklich gelöscht. Ein anschließendes G0 plant Leistung null.
Das erklärt das beobachtete Verhalten; der genaue Host-Dialog ist damit
noch nicht nachgewiesen.

## Korrektur

- Der ISR merkt sich lokal, ob gerade ein Inline-Block abgeschlossen wurde.
  Wenn danach kein ausführbarer Bewegungsblock verfügbar ist, wird die
  physische PWM direkt auf null gesetzt. Das gilt auch, wenn nur noch
  Positions-Synchronisationsblöcke folgen oder der Planner die Lieferung
  einer Folgebewegung vorübergehend zurückhält.
- Direkt aufeinanderfolgende Inline-Blöcke behalten ihre jeweilige Ausgabe;
  es wird kein zusätzlicher Aus-Puls zwischen solchen Blöcken eingefügt.
  Ein folgender nicht-inline Block erbt keine alte Inline-Leistung.
- Die ISR-sichere Abschaltung enthält keine CAN-Nachricht, keine Wartezeit
  und keine Lüftersteuerung. Sie setzt Ausgang und On/Off-Zustand zurück,
  erhält aber den angeforderten Leistungswert für spätere Befehle.
- Ein periodischer Leerlauftest würde auch einen bewusst eingeschalteten
  Fokuspunkt löschen. Deshalb wird nur der Abschluss einer Inline-Bewegung
  behandelt; explizite stationäre Fire-/Fokusbefehle bleiben möglich.
- Planner Quick Stop (auch von M410 verwendet): Ausgang löschen, Inline-Modus
  deaktivieren und Abbruch des aktiven Blocks anfordern, bevor der Stepper-
  Interrupt wieder freigegeben wird. Die bisherige Reihenfolge enthielt
  zwischen Interrupt-Freigabe und Abbruchanforderung eine Lücke.
- M112/`kill` und direktes `minkill` sperren den Stepper-Interrupt und
  löschen den Laserausgang vor Diagnoseausgabe, Wartezeiten und globalem
  Interrupt-Stopp. Der PWM-Timer darf seinen alten Wert nicht weiter ausgeben.
- Stepper-Abbruch sowie Snapmakers Quick-Stop-/Not-Aus-ISR-Pfade löschen den
  Ausgang ebenfalls. Bei `Running == false` wird kein neuer normaler
  Bewegungsblock mit Laserleistung gestartet.

Der Abschaltpfad hat keine Kopf-Leistungs-Whitelist und verwendet denselben
PWM-Ausgang wie die Inline-Ausgabe aller vorhandenen Laserköpfe, einschließlich
2 W IR. Das ist eine Aussage zum Code, keine Hardware-Abnahme aller Köpfe.
Air Assist, Bewegungswerte und Kreuzlaser-Ansteuerung wurden nicht geändert.

## Grenzen

- Untersucht ist der normale Stepper-/Inline-Pfad bei deaktiviertem FT-Motion
  (Projektstandard). Aktives FT-Motion/Input Shaping ist für Laserbetrieb
  durch diese Prüfung nicht abgedeckt.
- Ein LightBurn-Pause-Klick ist für den Controller nicht erkennbar, wenn der
  Host lediglich keine weiteren Daten sendet. Dann laufen vorhandene Blöcke
  regulär aus; danach löscht LA02 den Ausgang. Keine garantierte sofortige
  Abschaltung ab Mausklick.
- Quick Stop verwirft den Bewegungspuffer. Das ist kein vollständiges
  Kommunikations-Abbruchprotokoll: später aus dem seriellen Eingangs-/G-Code-
  Puffer oder vom Host eintreffende neue Befehle sind gesondert zu prüfen.
- Kein nachgewiesener Schutz gegen alle USB-, Hardware- oder Firmwarefehler.
- Sofortiger optischer Leistungsabfall und genaue Reaktionszeit müssen am
  realen PWM-Signal bzw. geeigneten Messaufbau geprüft werden. Ein bloßer
  sichtbarer Positionsstopp ist kein Nachweis der Laserabschaltung.

## Softwareprüfung

Erfolgreich in der vorhandenen Linux-Umgebung:

- Firmware-Build `pio run -e GD32F105`.
- Paketierung `pio run -e GD32F105 -t pack`.
- Paketkopf, Controller-Typ, Offset, Länge, Prüfsumme und unveränderte
  Einbettung des Rohimages geprüft.
- `python -m unittest discover -s tests -p 'test_*.py' -v`.
- `git diff --check`.

Der neue Host-Test kompiliert vollständige Produktionsfunktionen
`BlankOutput_ISR`, `TurnOn_ISR`, `finish_inline_laser_block` und
`Planner::quick_stop` sowie der Kill-Helfer gegen einen simulierten PWM-Ausgang und Interrupt-Hooks.
Er prüft Ausgang null nach Blockende, Erhalt des Sollwerts, Wiederausgabe
beim Folgeblock, Übergang zu Nicht-Inline, stationären Fokus und die
Quick-Stop-Reihenfolge und Abschaltung vor dem Kill. Offline-Objekte dürfen den PWM-Ausgang nicht berühren.

**Testgrenze:** Das ist keine vollständige Simulation des Stepper-Interrupts,
der FreeRTOS-Parallelität, des LightBurn-Dialogs oder des Werkzeugkopfmoduls.
Die Aufrufstellen wurden im Quellcode geprüft und für den MCU-Build kompiliert.

LA02 RAM: 82.688 / 98.304 Bytes; Flash: 297.928 / 524.288 Bytes.
Lokales Testpaket: `Snapmaker_V5.2.1-LA02_20261120.bin`, 300.024 Bytes.
SHA-256: `c1df27222f11e51fde1f31916b1619f935f5bda34651c64adc781299af493cbe`.
Kein Binärrelease veröffentlicht, kein Hardwaretest von LA02 durchgeführt.

## Nächste Abnahme

Zuerst ohne Laseremission den Host-Dialog bei Pause und Stop getrennt
aufzeichnen; keine erneute Reproduktion des Fehlers mit Bearbeitungsleistung.
Dann den PWM-Ausgang in einem geeigneten Aufbau ohne emittierende Quelle
prüfen. Dabei keine Werkzeugkopfanschlüsse unter Spannung trennen.

Zu prüfen: Ende des letzten Blocks ohne M5, Pause nach Auslaufen des Puffers,
Fortsetzen mit neuem Block, Stop/M410, Synchronisationsblöcke, normale
Raster-/Linienübergänge und bewusstes stationäres Fokuslicht. Bei Stop auch
nachlaufende serielle Befehle erfassen. Anschließend getrennte Kopf-Abnahme
für 1,6 W, 10 W, 40 W und 2 W IR. Gehäuse-/Türfunktionen bleiben zusätzlich
Teil der Abnahme.
