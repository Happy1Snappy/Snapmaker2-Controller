"""Check real package headers and payloads without flashing hardware."""
import contextlib
import datetime
import importlib.util
import io
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('firmware_pack', ROOT / 'snapmaker/scripts/pack.py')
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)


class FirmwarePackageTest(unittest.TestCase):
    def test_controller_package_versions_and_payload(self):
        for version in ('V5.2.1', 'V5.2.1-LA01', 'V5.2.1-LA03'):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                payload = bytes(range(256)) * 3
                raw = root / 'firmware.bin'
                raw.write_bytes(payload)
                (root / "firmware.elf").write_bytes(b"test ELF placeholder")
                with contextlib.redirect_stdout(io.StringIO()):
                    minor = pack.pack_minor_controller_image(raw, root, version)
                    pack.pack_major_image(controller=minor)
                date = datetime.datetime.today().strftime('%Y%m%d')
                major = root / 'release' / ('Snapmaker_' + version + '_' + date + '.bin')
                data = major.read_bytes()
                self.assertEqual(struct.unpack_from('>h', data)[0], 48)
                self.assertEqual(data[2:34].rstrip(b'\0').decode(), 'Snapmaker_' + version + '_' + date)
                self.assertEqual(data[38], 1)
                kind, offset, length = struct.unpack_from('>bii', data, 39)
                self.assertEqual((kind, offset, length), (0, 48, 2048 + len(payload)))
                image = data[offset:offset + length]
                self.assertEqual(image, minor.read_bytes())
                self.assertEqual(image[5:38].rstrip(b'\0').decode(), 'Snapmaker_' + version)
                self.assertEqual(struct.unpack_from('<ii', image, 40), (len(payload), sum(payload) & 0xFFFFFFF))
                self.assertEqual(image[2048:], payload)


if __name__ == '__main__':
    unittest.main()
