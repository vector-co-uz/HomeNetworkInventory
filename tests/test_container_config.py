"""Run: python -m unittest discover -s tests -v (requires httpx)."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROBE = r'''
import os
from fastapi.testclient import TestClient
from docker.container_app import app
from app.database import SessionLocal, engine
from app.models.site import Site
from app.models.user import User

secure = os.environ['SESSION_HTTPS_ONLY'] == 'true'
phase = os.environ['TEST_PHASE']
with TestClient(app, base_url='https://testserver' if secure else 'http://testserver') as client:
    assert client.get('/login').status_code == 200
    assert client.get('/static/css/custom.css').status_code == 200
    password = 'Admin' if phase == 'first' else 'container-test-password'
    response = client.post('/login', data={'username': 'Admin', 'password': password}, follow_redirects=False)
    assert response.status_code == 303
    assert ('secure' in response.headers['set-cookie'].lower()) == secure
    if phase == 'first':
        assert client.get('/', follow_redirects=False).headers['location'] == '/change-password'
        response = client.post('/change-password', data={
            'old_password': 'Admin', 'new_password': 'container-test-password',
            'confirm_password': 'container-test-password'}, follow_redirects=False)
        assert response.status_code == 303
        with SessionLocal() as db:
            db.add(Site(name='Persistent home', photo=b'photo-data', photo_mime='image/png'))
            db.commit()
    else:
        with SessionLocal() as db:
            assert db.query(User).count() == 1
            assert not db.query(User).one().must_change_password
            assert db.query(Site).one().photo == b'photo-data'
    assert client.get('/sites').status_code == 200
engine.dispose()
'''


class ContainerConfigTests(unittest.TestCase):
    def run_code(self, code, env, success=True):
        result = subprocess.run([sys.executable, '-c', code], cwd=ROOT,
                                env=env, text=True, capture_output=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_requires_secret(self):
        for value in ['', 'short']:
            env = dict(os.environ, SESSION_SECRET=value)
            result = self.run_code('import docker.container_app', env, success=False)
            self.assertIn('Set SESSION_SECRET', result.stderr)

    def test_rejects_invalid_boolean(self):
        env = dict(os.environ, SESSION_SECRET='x' * 48, SESSION_HTTPS_ONLY='typo')
        result = self.run_code('import docker.container_app', env, success=False)
        self.assertIn('SESSION_HTTPS_ONLY must be', result.stderr)

    def test_http_https_and_database_persistence(self):
        for secure in ['false', 'true']:
            with self.subTest(https=secure), tempfile.TemporaryDirectory() as tmp:
                database = Path(tmp) / 'inventory.db'
                env = dict(os.environ, SESSION_SECRET='test-secret-' * 4,
                           SESSION_HTTPS_ONLY=secure,
                           DATABASE_URL='sqlite:///' + database.as_posix())
                for phase in ['first', 'restart']:
                    self.run_code(PROBE, dict(env, TEST_PHASE=phase))
                self.assertTrue(database.exists())


if __name__ == '__main__':
    unittest.main()
