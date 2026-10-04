"""Collect public URI subscriptions; Mihomo parses and tests actual proxy traffic.

No subscription-conversion service receives node credentials. Outputs change only
after a nonempty successful benchmark. Requires Python 3.11+, curl and Mihomo.
"""
import base64
import concurrent.futures
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import random
import re
import secrets
import socket
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
URI_RE = re.compile(r'(?:vmess|vless|trojan|ss|hysteria2|hy2)://[^\s<>"`]+')


def b64decode(value):
    value = value.strip()
    return base64.b64decode(value + '=' * (-len(value) % 4), altchars=b'-_', validate=True).decode('utf-8')


def extract(text):
    found = URI_RE.findall(text)
    if not found:
        try:
            found = URI_RE.findall(b64decode(re.sub(r'\s+', '', text)))
        except (ValueError, UnicodeError):
            pass
    return found


def public_host(host):
    if not host or host.lower() in {'localhost', 'localhost.localdomain'} or host.endswith('.local'):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        return True


def normalize(uri):
    """Preserve protocol fields; only rewrite display name. Core does conversion."""
    scheme = uri.split('://', 1)[0]
    if scheme == 'vmess':
        obj = json.loads(b64decode(uri.split('://', 1)[1]))
        host, port = obj['add'], int(obj['port'])
        if any(str(obj.get(k, '')).lower() in {'true', '1'} for k in ['allowInsecure', 'insecure', 'skip-cert-verify']):
            raise ValueError('insecure TLS')
        obj.pop('ps', None)
        canonical = json.dumps(obj, sort_keys=True, separators=(',', ':'))
        key = hashlib.sha256(canonical.encode()).hexdigest()[:20]
        obj['ps'] = 'n-' + key
        named = 'vmess://' + base64.b64encode(json.dumps(obj, separators=(',', ':')).encode()).decode()
    else:
        parsed = urllib.parse.urlsplit(uri)
        q = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if any(k.lower() in {'allowinsecure', 'insecure', 'skip-cert-verify'} and v.lower() in {'true', '1'} for k, v in q):
            raise ValueError('insecure TLS')
        host, port = parsed.hostname, parsed.port
        if scheme == 'ss' and '@' not in parsed.netloc:
            decoded = b64decode(parsed.netloc)
            endpoint = urllib.parse.urlsplit('ss://' + decoded)
            host, port = endpoint.hostname, endpoint.port
        if scheme not in {'vless', 'trojan', 'ss', 'hysteria2', 'hy2'}:
            raise ValueError('unsupported protocol')
        canonical = urllib.parse.urlunsplit(('hysteria2' if scheme == 'hy2' else scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(sorted(q)), ''))
        key = hashlib.sha256(canonical.encode()).hexdigest()[:20]
        named = uri.split('#', 1)[0] + '#n-' + key
    if not public_host(host) or port is None or not 1 <= port <= 65535:
        raise ValueError('invalid endpoint')
    return 'n-' + key, named, host


def rename(uri, name):
    if uri.startswith('vmess://'):
        obj = json.loads(b64decode(uri[8:]))
        obj['ps'] = name
        return 'vmess://' + base64.b64encode(json.dumps(obj, separators=(',', ':')).encode()).decode()
    return uri.split('#', 1)[0] + '#' + urllib.parse.quote(name, safe='')


def fetch_source(url):
    if not url.startswith('https://'):
        raise ValueError('sources must use HTTPS')
    result = subprocess.run(['curl', '--silent', '--show-error', '--fail', '--location', '--proto', '=https', '--proto-redir', '=https',
                             '--max-time', '25', '--max-filesize', str(16 * 1024 * 1024), '--user-agent', 'free-node-sub/1.0', url],
                            capture_output=True, timeout=28, check=True)
    if len(result.stdout) > 16 * 1024 * 1024:
        raise ValueError('source too large')
    return extract(result.stdout.decode('utf-8-sig'))


def resolve_public(host):
    try:
        addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        return bool(addresses) and all(ipaddress.ip_address(a[4][0]).is_global for a in addresses)
    except (OSError, ValueError):
        return False


def configuration(provider, testing=False, secret=''):
    groups = [{'name': '节点选择', 'type': 'select', 'use': ['checked']}]
    if not testing:
        groups.insert(0, {'name': '自动选择', 'type': 'url-test', 'use': ['checked'], 'url': 'https://www.gstatic.com/generate_204', 'interval': 300, 'tolerance': 80})
        groups[1]['proxies'] = ['自动选择']
    config = {'mixed-port': 17890 if testing else 7890, 'allow-lan': False,
              'mode': 'rule', 'log-level': 'silent' if testing else 'info',
              'proxy-providers': {'checked': provider}, 'proxy-groups': groups,
              'rules': ['MATCH,节点选择'] if testing else ['IP-CIDR,127.0.0.0/8,DIRECT,no-resolve', 'IP-CIDR,10.0.0.0/8,DIRECT,no-resolve', 'IP-CIDR,172.16.0.0/12,DIRECT,no-resolve', 'IP-CIDR,192.168.0.0/16,DIRECT,no-resolve', 'MATCH,节点选择']}
    if testing:
        config.update({'external-controller': '127.0.0.1:19090', 'secret': secret})
    return config


def test_configuration(nodes, work, secret):
    # A malformed URI can reject a whole Mihomo provider. Load each candidate
    # separately so one broken public entry cannot discard all valid nodes.
    providers = {}
    for name, uri in nodes.items():
        filename = name + '.txt'
        (work / filename).write_text(uri, encoding='utf-8')
        providers[name] = {'type': 'file', 'path': './' + filename, 'override': {'skip-cert-verify': False}}
    config = configuration({}, True, secret)
    config['proxy-providers'] = providers
    config['proxy-groups'][0]['use'] = list(providers)
    return config


def api(secret, path, method='GET', body=None, timeout=10):
    req = urllib.request.Request('http://127.0.0.1:19090' + path, data=None if body is None else json.dumps(body).encode(), method=method,
                                 headers={'Authorization': 'Bearer ' + secret, 'Content-Type': 'application/json'})
    with OPENER.open(req, timeout=timeout) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


def delay_test(secret, name, settings):
    try:
        query = urllib.parse.urlencode({'url': settings['test_url'], 'timeout': settings['max_delay_ms'], 'expected': '204'})
        encoded = urllib.parse.quote(name, safe='')
        result = api(secret, '/providers/proxies/' + encoded + '/' + encoded + '/healthcheck?' + query)
        delay = result.get('delay', 0)
        return (delay, name) if 0 < delay <= settings['max_delay_ms'] else None
    except Exception:
        return None


def download_test(settings):
    # Always use the selected proxy. HTTPS verifies the target certificate.
    result = subprocess.run(['curl', '--silent', '--show-error', '--fail', '--proxy', 'http://127.0.0.1:17890', '--noproxy', '',
                             '--connect-timeout', '5', '--max-time', str(settings['download_timeout_s']),
                             '--max-filesize', str(settings['download_bytes']), '--output', os.devnull,
                             '--write-out', '%{json}', settings['download_url']], capture_output=True, text=True, timeout=settings['download_timeout_s'] + 3)
    if result.returncode:
        return None
    stats = json.loads(result.stdout)
    if stats['http_code'] != 200 or stats['size_download'] != settings['download_bytes']:
        return None
    kib = stats['size_download'] / max(stats['time_total'], 0.001) / 1024
    return round(kib, 1) if kib >= settings['min_speed_kib_s'] else None


def publish(results, nodes, settings, report):
    if not results:
        raise RuntimeError('No node passed HTTPS download tests; previous subscription retained')
    results = sorted(results, key=lambda r: (-r['speed_kib_s'], r['delay_ms']))[:settings['max_output']]
    uris = []
    for i, r in enumerate(results, 1):
        label = f"{i:02d} | {r['speed_kib_s']} KiB/s | {r['delay_ms']} ms"
        uris.append(rename(nodes[r['name']], label))
        r['name'] = label
    provider = {'type': 'http', 'url': settings['subscription_base'] + '/v2ray.txt', 'path': './providers/free-node-sub.txt', 'interval': 14400,
                'override': {'skip-cert-verify': False}, 'health-check': {'enable': True, 'url': settings['test_url'], 'interval': 300}}
    report.update({'status': 'success', 'published': len(uris), 'nodes': results})
    files = {'nodes.txt': '\n'.join(uris) + '\n',
             'v2ray.txt': base64.b64encode(('\n'.join(uris) + '\n').encode()).decode() + '\n',
             'clash.yaml': json.dumps(configuration(provider), ensure_ascii=False, indent=2) + '\n',
             'report.json': json.dumps(report, ensure_ascii=False, indent=2) + '\n'}
    out = ROOT / 'output'
    out.mkdir(exist_ok=True)
    for name, contents in files.items():
        temp = out / (name + '.tmp')
        temp.write_text(contents, encoding='utf-8')
        temp.replace(out / name)


def main():
    settings = json.loads((ROOT / 'auto_sub/settings.json').read_text())
    report = {'tested_at_utc': datetime.now(timezone.utc).isoformat(),
              'location': os.getenv('RUNNER_NAME', 'local execution environment'),
              'measurement': 'HTTPS 1 MiB short download including handshake; not sustained bandwidth; not user-local reachability',
              'thresholds': {k: settings[k] for k in ['max_delay_ms', 'min_speed_kib_s', 'download_bytes']}, 'sources': []}
    nodes, hosts, recent = {}, {}, set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fetch_source, url): url for url in settings['sources']}
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                uris = future.result()
                report['sources'].append({'url': url, 'fetched': len(uris)})
                for uri in uris:
                    try:
                        name, normalized, host = normalize(uri)
                        nodes[name], hosts[name] = normalized, host
                        if url in settings['sources'][:3]:
                            recent.add(name)
                    except Exception:
                        pass
            except Exception as e:
                report['sources'].append({'url': url, 'error': type(e).__name__})
    report['unique_candidates'] = len(nodes)
    print('Source results:', json.dumps(report['sources']), flush=True)
    print('Collected unique candidates:', len(nodes), flush=True)
    # Recheck previously selected nodes first; rotate a bounded sample of new nodes.
    previous = ROOT / 'output/nodes.txt'
    priority = []
    if previous.exists():
        for uri in extract(previous.read_text()):
            try:
                name, _, _ = normalize(uri)
                if name in nodes and name not in priority:
                    priority.append(name)
            except Exception:
                pass
    priority.extend(sorted(recent - set(priority)))
    remaining = sorted(set(nodes) - set(priority))
    random.Random(datetime.now(timezone.utc).strftime('%Y%m%d%H')).shuffle(remaining)
    names = (priority + remaining)[:settings['max_candidates']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        valid = dict(zip(names, pool.map(resolve_public, [hosts[n] for n in names])))
    nodes = {n: nodes[n] for n in names if valid[n]}
    if not nodes:
        raise RuntimeError('No candidates; previous subscription retained')
    secret = secrets.token_hex(24)
    with tempfile.TemporaryDirectory(prefix='free-node-sub-') as folder:
        work = Path(folder)
        (work / 'config.json').write_text(json.dumps(test_configuration(nodes, work, secret)))
        binary = str(Path(os.environ.get('MIHOMO_BIN', '/tmp/free-node-mihomo')).resolve())
        with (work / 'core.log').open('w') as log:
            subprocess.run([binary, '-t', '-d', folder, '-f', str(work / 'config.json')], stdout=log, stderr=log, check=True, timeout=30)
            proc = subprocess.Popen([binary, '-d', folder, '-f', str(work / 'config.json')], stdout=log, stderr=log)
            try:
                stable, previous_count = 0, -1
                for _ in range(100):
                    if proc.poll() is not None:
                        raise RuntimeError('Mihomo exited during startup')
                    try:
                        providers = api(secret, '/providers/proxies')['providers']
                        loaded = [p for k, v in providers.items() if k in nodes for p in v.get('proxies', [])]
                        stable = stable + 1 if len(loaded) == previous_count else 0
                        previous_count = len(loaded)
                        if loaded and stable >= 5:
                            break
                        time.sleep(0.2)
                    except Exception:
                        time.sleep(0.1)
                else:
                    raise RuntimeError('Mihomo startup timeout')
                names = [p['name'] for p in loaded if p['name'] in nodes]
                report['core_loaded'] = len(names)
                print('Core loaded:', len(names), flush=True)
                with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
                    delays = list(pool.map(lambda n: delay_test(secret, n, settings), names))
                alive = sorted(r for r in delays if r)
                report['https_latency_passed'] = len(alive)
                print('HTTPS latency passed:', len(alive), flush=True)
                results = []
                for index, (delay, name) in enumerate(alive[:settings['max_download_tests']], 1):
                    api(secret, '/proxies/' + urllib.parse.quote('节点选择', safe=''), 'PUT', {'name': name})
                    api(secret, '/connections', 'DELETE')
                    speed = download_test(settings)
                    print(f'Download test {index}: ' + ('passed' if speed else 'failed'), flush=True)
                    if speed:
                        results.append({'name': name, 'delay_ms': delay, 'speed_kib_s': speed})
                report['download_tested'] = min(len(alive), settings['max_download_tests'])
                report['download_passed'] = len(results)
                publish(results, nodes, settings, report)
                print('Published:', min(len(results), settings['max_output']), flush=True)
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
    

if __name__ == '__main__':
    main()
