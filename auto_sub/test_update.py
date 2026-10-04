import base64
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import update

SS = 'ss://YWVzLTI1Ni1nY206dGVzdA==@1.1.1.1:443#first'
VLESS = 'vless://00000000-0000-4000-8000-000000000001@1.1.1.1:443?security=reality&sni=example.com&pbk=ZmFrZS1wdWJsaWMta2V5&sid=ab&type=tcp#first'


class SubscriptionTests(unittest.TestCase):
    def test_extract_base64_and_malformed(self):
        self.assertEqual(update.extract(base64.b64encode((SS + '\n' + VLESS).encode()).decode()), [SS, VLESS])
        self.assertEqual(update.extract('not a subscription'), [])

    def test_duplicate_names_and_query_order(self):
        self.assertEqual(update.normalize(SS)[0], update.normalize(SS.replace('#first', '#second'))[0])
        a = 'vless://id@1.1.1.1:443?type=ws&path=%2Fhello#one'
        b = 'vless://id@1.1.1.1:443?path=%2Fhello&type=ws#two'
        self.assertEqual(update.normalize(a)[0], update.normalize(b)[0])

    def test_protocol_fields_preserved(self):
        _, normalized, _ = update.normalize(VLESS)
        self.assertEqual(normalized.split('#')[0], VLESS.split('#')[0])
        vm = {'add': '1.1.1.1', 'port': '443', 'id': '00000000-0000-4000-8000-000000000001', 'net': 'ws', 'path': '/abc', 'tls': 'tls', 'host': 'example.com', 'ps': 'old', 'aid': '0', 'scy': 'auto'}
        uri = 'vmess://' + base64.b64encode(json.dumps(vm).encode()).decode()
        _, normalized, _ = update.normalize(uri)
        renamed = json.loads(update.b64decode(update.rename(normalized, 'new')[8:]))
        self.assertEqual(renamed, dict(vm, ps='new'))

    def test_private_endpoints_and_insecure_tls_rejected(self):
        for uri in ['vless://id@127.0.0.1:443', 'trojan://pw@10.0.0.1:443', 'trojan://pw@1.1.1.1:443?allowInsecure=1', 'vless://id@[::1]:443', 'ss://bad']:
            with self.subTest(uri=uri), self.assertRaises(Exception):
                update.normalize(uri)

    def test_no_pass_retains_previous_output(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(update, 'ROOT', Path(folder)):
            out = Path(folder) / 'output'
            out.mkdir()
            original = out / 'v2ray.txt'
            original.write_text('previous')
            with self.assertRaises(RuntimeError):
                update.publish([], {}, {}, {})
            self.assertEqual(original.read_text(), 'previous')
            self.assertEqual(list(out.iterdir()), [original])

    def test_both_formats_contain_same_ranked_nodes(self):
        settings = json.loads((update.ROOT / 'auto_sub/settings.json').read_text())
        n, uri, _ = update.normalize(SS)
        with tempfile.TemporaryDirectory() as folder, patch.object(update, 'ROOT', Path(folder)):
            update.publish([{'name': n, 'delay_ms': 50, 'speed_kib_s': 1000}], {n: uri}, settings, {})
            output = Path(folder) / 'output'
            plain = (output / 'nodes.txt').read_text()
            self.assertEqual(update.b64decode((output / 'v2ray.txt').read_text()), plain)
            config = json.loads((output / 'clash.yaml').read_text())
            self.assertEqual(config['proxy-providers']['checked']['url'], settings['subscription_base'] + '/v2ray.txt')
            self.assertEqual(config['rules'][-1], 'MATCH,节点选择')
            binary = os.environ.get('MIHOMO_BIN', '/tmp/free-node-mihomo')
            if Path(binary).is_file():
                # Validate the generated Clash config and native URI provider.
                config['proxy-providers']['checked'] = {'type': 'file', 'path': './nodes.txt'}
                (output / 'config.json').write_text(json.dumps(config))
                result = subprocess.run([binary, '-t', '-d', str(output), '-f', str(output / 'config.json')], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_native_core_loads_uri_names(self):
        binary = os.environ.get('MIHOMO_BIN', '/tmp/free-node-mihomo')
        if not Path(binary).is_file():
            self.skipTest('Mihomo not installed')
        name, uri, _ = update.normalize(SS)
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            (p / 'nodes.txt').write_text(uri)
            cfg = update.configuration({'type': 'file', 'path': './nodes.txt'}, True, 'fixture')
            (p / 'config.json').write_text(json.dumps(cfg))
            proc = subprocess.Popen([binary, '-d', folder, '-f', str(p / 'config.json')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                loaded = []
                for _ in range(100):
                    try:
                        loaded = update.api('fixture', '/providers/proxies/checked')['proxies']
                        if loaded:
                            break
                    except Exception:
                        pass
                    time.sleep(0.05)
                self.assertEqual([item['name'] for item in loaded], [name])
            finally:
                proc.terminate()
                proc.wait(timeout=5)

    def test_invalid_native_uri_does_not_poison_valid_nodes(self):
        binary = os.environ.get('MIHOMO_BIN', '/tmp/free-node-mihomo')
        if not Path(binary).is_file():
            self.skipTest('Mihomo not installed')
        name, uri, _ = update.normalize(SS)
        bad = 'ss://' + base64.b64encode(b'unknown-cipher:pw').decode() + '@1.1.1.1:443#bad'
        bad_name, bad_uri, _ = update.normalize(bad)
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            cfg = update.test_configuration({name: uri, bad_name: bad_uri}, p, 'fixture')
            (p / 'config.json').write_text(json.dumps(cfg))
            proc = subprocess.Popen([binary, '-d', folder, '-f', str(p / 'config.json')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                loaded = []
                for _ in range(100):
                    try:
                        providers = update.api('fixture', '/providers/proxies')['providers']
                        loaded = [item['name'] for k, v in providers.items() if k in {name, bad_name} for item in v['proxies']]
                        if name in loaded:
                            break
                    except Exception:
                        pass
                    time.sleep(0.05)
                self.assertEqual(loaded, [name])
            finally:
                proc.terminate()
                proc.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
