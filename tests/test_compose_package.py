import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location(
    'package_compose', Path(__file__).resolve().parents[1] / 'scripts/package_compose.py')
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class ComposePackageTests(unittest.TestCase):
    def test_bundle_can_deploy_without_source_or_secrets(self):
        image = 'ghcr.io/vector-co-uz/homenetworkinventory@sha256:' + 'a' * 64
        with tempfile.TemporaryDirectory() as directory:
            archive = packager.build(image, Path(directory))
            with zipfile.ZipFile(archive) as bundle:
                self.assertIsNone(bundle.testzip())
                self.assertIn('.env.example', bundle.namelist())
                self.assertNotIn('.env', bundle.namelist())
                compose = bundle.read('compose.yaml').decode()
                self.assertIn('image: ' + image, compose)
                self.assertNotIn('build:', compose)
                self.assertIn('hni_data:/data', compose)
                self.assertIn('SESSION_SECRET=', bundle.read('.env.example').decode())

    def test_rejects_mutable_or_malformed_image(self):
        with tempfile.TemporaryDirectory() as directory:
            for image in ['ghcr.io/owner/repo:latest', 'bad\nimage: injected']:
                with self.assertRaises(ValueError):
                    packager.build(image, Path(directory))
