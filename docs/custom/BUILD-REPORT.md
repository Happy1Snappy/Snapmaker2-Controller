# LA01 build verification — 2026-11-17

The table below records the original build verification before machine testing.
For subsequent owner-reported Windows and hardware results, see
[the current usage and test notes](README.de.md).

Upstream base: `314c167b0a1ce331d867b10abd32e00908e4aa9c` (`v5.2.1`).
Environment: Linux x86_64, Python 3.12.14, PlatformIO Core 6.2.0.
Pinned target dependencies: ststm32 20.0.0, GCC ARM 1.70201.0,
Arduino STM32 Maple 3.10000.201129.

| Check | Result |
| --- | --- |
| Unmodified upstream build, GD32F105 | PASS |
| LA01 build, GD32F105 | PASS |
| `pio run -e GD32F105 -t pack` | PASS |
| Package regression test: original and custom version | PASS |
| Real package: version, type, offset, length, checksum and raw payload | PASS |
| `git diff --check` | PASS |
| Windows build | NOT TESTED |
| Machine, USB streaming, pump, door, touchscreen | NOT TESTED |
| LightBurn profiles, framing, inline | NOT TESTED |

Baseline RAM: 82,688 / 98,304 bytes; flash: 297,520 / 524,288 bytes.
LA01 RAM: 82,688 / 98,304 bytes; flash: 297,672 / 524,288 bytes.
RAM headroom is unchanged; runtime behavior has not been measured.

The inherited packager mistakenly included the source filename's date and
`.bin` extension in the major-image version. The version match now excludes
that suffix. The regression test checks the actual binary headers and payload
for stable and custom versions:

```sh
python -m unittest discover -s tests -p test_firmware_pack.py -v
```

Local experimental package: `Snapmaker_V5.2.1-LA01_20261117.bin`.
Size: 299,768 bytes.
SHA-256: `1b86ff21f542c4d39f6b20a59c64bc4c1147fd8aa1c76a1ff04d91ff871eda55`.
This records the package built in this environment; rebuilds may differ.
No flash operation was performed during this build verification. The owner has
since installed and tested LA01; see the linked usage notes. No binary release
is published.
