import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from aidesktop.newelle_client import NewelleError, check_newelle, complete_newelle


class FakeNewelle(BaseHTTPRequestHandler):
    requests = []

    def do_GET(self):
        if self.path != '/v1/models':
            self.send_error(404)
            return
        self.reply({'data': [{'id': 'my-selected-model'}]})

    def do_POST(self):
        if self.path != '/v1/chat/completions':
            self.send_error(404)
            return
        data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        type(self).requests.append((data, self.headers.get('Authorization')))
        self.reply({'choices': [{'message': {'role': 'assistant', 'content': '{"kind":"final","message":"Ready"}'}}]})

    def reply(self, obj):
        content = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *_args):
        return


class NewelleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), FakeNewelle)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_health_and_model_inference_have_no_tool_calls(self):
        FakeNewelle.requests.clear()
        with patch.dict(os.environ, {
            'AIDESKTOP_NEWELLE_PORT': str(self.server.server_port),
            'AIDESKTOP_NEWELLE_API_KEY': 'test-private-key',
        }):
            self.assertIn('my-selected-model', check_newelle())
            self.assertEqual(complete_newelle('System constraints', 'User question'), '{"kind":"final","message":"Ready"}')
        payload, auth = FakeNewelle.requests[-1]
        self.assertEqual(auth, 'Bearer test-private-key')
        self.assertNotIn('tools', payload)
        self.assertNotIn('model', payload)
        self.assertEqual(payload['messages'][0], {'role':'system','content':'System constraints'})
        self.assertEqual(payload['messages'][1], {'role':'user','content':'User question'})
        self.assertIs(payload['stream'], False)

    def test_reads_private_token_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            location = Path(tmp) / 'ai-desktop'
            location.mkdir()
            (location / 'newelle-token').write_text('test-private-key\n', encoding='utf-8')
            with patch.dict(os.environ, {
                'XDG_CONFIG_HOME': tmp, 'AIDESKTOP_NEWELLE_PORT': str(self.server.server_port),
                'AIDESKTOP_NEWELLE_API_KEY': '',
            }):
                self.assertIn('connected', check_newelle())

    def test_requires_explicit_shared_api_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {
                'AIDESKTOP_NEWELLE_PORT': str(self.server.server_port),
                'AIDESKTOP_NEWELLE_API_KEY':'', 'XDG_CONFIG_HOME':tmp,
            }):
                with self.assertRaisesRegex(NewelleError, 'Configure a Newelle GUI API key'):
                    check_newelle()

    def test_port_restrictions(self):
        for value in ('bad', '-1', '0', '65536'):
            with self.subTest(port=value), patch.dict(os.environ, {
                'AIDESKTOP_NEWELLE_PORT': value, 'AIDESKTOP_NEWELLE_API_KEY':'test-private-key'
            }):
                with self.assertRaises(NewelleError):
                    check_newelle()

    def test_unavailable_service_error(self):
        with patch.dict(os.environ, {
            'AIDESKTOP_NEWELLE_PORT': '1', 'AIDESKTOP_NEWELLE_API_KEY':'test-private-key'
        }):
            with self.assertRaisesRegex(NewelleError, 'unavailable'):
                check_newelle()


if __name__ == '__main__':
    unittest.main()
