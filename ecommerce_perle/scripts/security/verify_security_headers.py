#!/usr/bin/env python
import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


def fetch(url, timeout=15):
    request = Request(
        url=url,
        method='GET',
        headers={
            'User-Agent': 'perle-security-headers-check/1.0',
            'X-Forwarded-Proto': 'https',
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode('utf-8', errors='replace')
            return response.status, dict(response.headers.items()), body
    except HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        return exc.code, dict(exc.headers.items()), body
    except URLError as exc:
        return None, {}, str(exc)


def normalize_headers(headers):
    return {k.lower(): v for k, v in headers.items()}


def normalize_path(raw_path):
    if not raw_path:
        return ''
    parsed = urlparse(raw_path)
    candidate = parsed.path if parsed.scheme and parsed.netloc else raw_path
    if not candidate.startswith('/'):
        candidate = f'/{candidate}'
    return candidate


def discover_confirmation_path(dast_report_path):
    if not dast_report_path:
        return ''

    report_path = Path(dast_report_path)
    if not report_path.exists():
        return ''

    try:
        payload = json.loads(report_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return ''

    for check in payload.get('checks', []):
        if check.get('id') != 'order_confirmation_idor':
            continue
        confirmation_url = check.get('confirmation_url', '')
        return normalize_path(confirmation_url)
    return ''


def resolve_paths(args):
    if args.paths:
        paths = [normalize_path(path) for path in args.paths if normalize_path(path)]
    else:
        paths = ['/', '/cart/', '/checkout/']
        if args.scope == 'full':
            paths.append('/admin/login/')

    confirmation_path = discover_confirmation_path(args.dast_report)
    if confirmation_path:
        paths.append(confirmation_path)

    deduped_paths = []
    seen = set()
    for path in paths:
        if path in seen:
            continue
        deduped_paths.append(path)
        seen.add(path)
    return deduped_paths


def main():
    parser = argparse.ArgumentParser(description='Verify security headers for public/admin pages.')
    parser.add_argument('--base-url', required=True, help='Example: http://127.0.0.1:8013')
    parser.add_argument('--out', required=True, help='JSON output path')
    parser.add_argument('--phase', default='monitor', choices=['monitor', 'enforce'])
    parser.add_argument('--scope', default='web', choices=['web', 'full'])
    parser.add_argument('--dast-report', help='Path to dast_auth_csrf.json to discover confirmation URL')
    parser.add_argument('--require-hsts', action='store_true')
    parser.add_argument(
        '--paths',
        nargs='*',
        default=None,
        help='Paths to verify',
    )
    args = parser.parse_args()

    findings = []
    checks = []

    required_headers = {
        'x-content-type-options': 'nosniff',
        'x-frame-options': 'DENY',
        'referrer-policy': None,
    }
    csp_header = 'content-security-policy-report-only' if args.phase == 'monitor' else 'content-security-policy'
    paths = resolve_paths(args)

    for path in paths:
        url = urljoin(args.base_url.rstrip('/') + '/', path.lstrip('/'))
        status_code, raw_headers, _body = fetch(url)
        headers = normalize_headers(raw_headers)
        path_check = {
            'path': path,
            'status_code': status_code,
            'headers': headers,
            'missing': [],
        }

        if status_code is None:
            findings.append(
                {
                    'id': f'headers_unreachable_{path}',
                    'severity': 'high',
                    'message': f'No se pudo consultar {path}.',
                }
            )
            checks.append(path_check)
            continue

        if status_code >= 500:
            findings.append(
                {
                    'id': f'server_error_{path}',
                    'severity': 'high',
                    'message': f'Endpoint {path} respondio {status_code}.',
                }
            )

        for header_name, expected in required_headers.items():
            current_value = headers.get(header_name)
            if not current_value:
                path_check['missing'].append(header_name)
                findings.append(
                    {
                        'id': f'missing_{header_name}_{path}',
                        'severity': 'high',
                        'message': f'Falta header {header_name} en {path}.',
                    }
                )
                continue
            if expected and current_value.lower() != expected.lower():
                findings.append(
                    {
                        'id': f'invalid_{header_name}_{path}',
                        'severity': 'medium',
                        'message': f'Header {header_name} invalido en {path}: {current_value}.',
                    }
                )

        if csp_header not in headers:
            path_check['missing'].append(csp_header)
            findings.append(
                {
                    'id': f'missing_{csp_header}_{path}',
                    'severity': 'high',
                    'message': f'Falta {csp_header} en {path}.',
                }
            )

        if args.require_hsts and 'strict-transport-security' not in headers:
            path_check['missing'].append('strict-transport-security')
            findings.append(
                {
                    'id': f'missing_hsts_{path}',
                    'severity': 'high',
                    'message': f'Falta Strict-Transport-Security en {path}.',
                }
            )

        checks.append(path_check)

    summary = {
        'critical': sum(1 for f in findings if f['severity'] == 'critical'),
        'high': sum(1 for f in findings if f['severity'] == 'high'),
        'medium': sum(1 for f in findings if f['severity'] == 'medium'),
        'low': sum(1 for f in findings if f['severity'] == 'low'),
    }

    report = {
        'tool': 'verify_security_headers',
        'phase': args.phase,
        'scope': args.scope,
        'base_url': args.base_url,
        'paths_checked': paths,
        'checks': checks,
        'findings': findings,
        'summary': summary,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

    print(
        f"Headers check -> critical={summary['critical']} high={summary['high']} "
        f"medium={summary['medium']} low={summary['low']}"
    )


if __name__ == '__main__':
    main()
