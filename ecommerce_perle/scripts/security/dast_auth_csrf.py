#!/usr/bin/env python
import argparse
import json
import time
from dataclasses import dataclass
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener


@dataclass
class HttpResponse:
    status_code: int | None
    headers: dict
    body: str


class HttpSession:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.cookies = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookies))

    def _full_url(self, path):
        return urljoin(self.base_url + '/', path.lstrip('/'))

    def request(self, method, path, *, json_data=None, form_data=None, headers=None, timeout=20):
        request_headers = {'User-Agent': 'perle-dast-auth-csrf/1.0'}
        if headers:
            request_headers.update(headers)

        body = None
        if json_data is not None:
            body = json.dumps(json_data).encode('utf-8')
            request_headers.setdefault('Content-Type', 'application/json')
        elif form_data is not None:
            body = urlencode(form_data).encode('utf-8')
            request_headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')

        request = Request(
            url=self._full_url(path),
            data=body,
            headers=request_headers,
            method=method.upper(),
        )

        try:
            with self.opener.open(request, timeout=timeout) as response:
                content = response.read().decode('utf-8', errors='replace')
                return HttpResponse(response.status, dict(response.headers.items()), content)
        except HTTPError as exc:
            content = exc.read().decode('utf-8', errors='replace')
            return HttpResponse(exc.code, dict(exc.headers.items()), content)
        except URLError as exc:
            return HttpResponse(None, {}, str(exc))

    def get_cookie(self, name):
        for cookie in self.cookies:
            if cookie.name == name:
                return cookie.value
        return ''

    def ensure_csrf(self, path='/'):
        self.request('GET', path)
        return self.get_cookie('csrftoken')


def _safe_json_loads(payload):
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _severity_counts(findings):
    return {
        'critical': sum(1 for finding in findings if finding['severity'] == 'critical'),
        'high': sum(1 for finding in findings if finding['severity'] == 'high'),
        'medium': sum(1 for finding in findings if finding['severity'] == 'medium'),
        'low': sum(1 for finding in findings if finding['severity'] == 'low'),
    }


def discover_variant_id(session):
    response = session.request('GET', '/api/products/')
    if response.status_code != 200:
        return None

    payload = _safe_json_loads(response.body)
    if not isinstance(payload, list):
        return None

    for product in payload:
        for variant in product.get('variants', []):
            if variant.get('stock', 0) > 0:
                return variant.get('id')
    return None


def check_cart_csrf(base_url):
    findings = []
    check = {'id': 'csrf_cart_mutation', 'passed': False}
    session = HttpSession(base_url)
    variant_id = discover_variant_id(session)
    check['variant_id'] = variant_id

    if not variant_id:
        findings.append(
            {
                'id': 'csrf_cart_setup_failed',
                'severity': 'high',
                'message': 'No se encontro variante con stock para prueba CSRF de carrito.',
            }
        )
        check['details'] = 'No hay variante disponible.'
        return check, findings

    response = session.request(
        'POST',
        '/api/cart/items/',
        json_data={'variant_id': variant_id, 'quantity': 1},
    )
    check['status_code'] = response.status_code

    if response.status_code == 403:
        check['passed'] = True
        check['details'] = 'Mutacion de carrito rechazada sin CSRF.'
    else:
        findings.append(
            {
                'id': 'csrf_cart_bypass',
                'severity': 'critical',
                'message': f'Carrito acepto mutacion sin CSRF (status {response.status_code}).',
            }
        )
        check['details'] = 'Posible bypass CSRF en carrito.'
    return check, findings


def check_checkout_csrf(base_url):
    findings = []
    check = {'id': 'csrf_checkout_confirm', 'passed': False}
    session = HttpSession(base_url)
    payload = {
        'full_name': 'Security QA',
        'email': f'csrf-checkout-{int(time.time())}@example.com',
        'phone': '',
        'line1': 'Calle QA',
        'city': 'Bogota',
        'state': 'DC',
        'coupon_code': '',
        'payment_method': 'whatsapp',
    }

    response = session.request(
        'POST',
        '/checkout/api/checkout/confirm/',
        json_data=payload,
    )
    check['status_code'] = response.status_code

    if response.status_code == 403:
        check['passed'] = True
        check['details'] = 'Checkout rechazo confirmacion sin CSRF.'
    else:
        findings.append(
            {
                'id': 'csrf_checkout_bypass',
                'severity': 'critical',
                'message': f'Checkout acepto confirmacion sin CSRF (status {response.status_code}).',
            }
        )
        check['details'] = 'Posible bypass CSRF en checkout.'
    return check, findings


def check_admin_bruteforce_lockout(base_url, failure_limit):
    findings = []
    check = {'id': 'admin_bruteforce_lockout', 'passed': False, 'failure_limit': failure_limit}
    session = HttpSession(base_url)
    lockout_detected = False
    lockout_attempt = None

    lockout_keywords = (
        'acceso temporalmente bloqueado',
        'demasiados intentos',
        'too many login attempts',
        'locked out',
        'temporarily blocked',
    )

    initial_login_page = session.request('GET', '/admin/login/')
    if initial_login_page.status_code != 200:
        findings.append(
            {
                'id': 'admin_lockout_setup_login_unavailable',
                'severity': 'high',
                'message': f'Login admin no disponible para prueba de lockout (status {initial_login_page.status_code}).',
            }
        )
        check['details'] = 'No se pudo cargar /admin/login/.'
        return check, findings

    for attempt in range(1, failure_limit + 3):
        csrf_token = session.ensure_csrf('/admin/login/')
        if not csrf_token:
            findings.append(
                {
                    'id': 'admin_lockout_setup_missing_csrf',
                    'severity': 'high',
                    'message': 'No se obtuvo csrftoken en login admin para prueba de lockout.',
                }
            )
            check['details'] = 'No se obtuvo token CSRF de admin.'
            return check, findings

        response = session.request(
            'POST',
            '/admin/login/?next=/admin/',
            form_data={
                'username': 'invalid-admin',
                'password': 'wrong-password-123',
                'this_is_the_login_form': '1',
                'next': '/admin/',
                'csrfmiddlewaretoken': csrf_token,
            },
            headers={
                'Referer': urljoin(base_url.rstrip('/') + '/', 'admin/login/'),
            },
        )
        body_lower = response.body.lower()
        has_lockout_message = any(keyword in body_lower for keyword in lockout_keywords)
        looks_like_csrf_error = response.status_code == 403 and 'csrf' in body_lower
        if response.status_code == 429 or has_lockout_message:
            lockout_detected = True
            lockout_attempt = attempt
            break
        if response.status_code == 403 and not looks_like_csrf_error:
            lockout_detected = True
            lockout_attempt = attempt
            break

    check['lockout_detected'] = lockout_detected
    check['lockout_attempt'] = lockout_attempt
    if lockout_detected:
        check['passed'] = True
        check['details'] = f'Lockout detectado en intento {lockout_attempt}.'
    else:
        findings.append(
            {
                'id': 'admin_bruteforce_no_lockout',
                'severity': 'high',
                'message': f'No se detecto lockout de admin tras {failure_limit + 2} intentos fallidos.',
            }
        )
        check['details'] = 'No hubo bloqueo progresivo observable.'
    return check, findings


def _extract_path_from_confirmation_url(confirmation_url):
    parsed = urlparse(confirmation_url)
    if parsed.scheme and parsed.netloc:
        return parsed.path
    if confirmation_url.startswith('/'):
        return confirmation_url
    return '/' + confirmation_url


def check_confirmation_idor(base_url):
    findings = []
    check = {'id': 'order_confirmation_idor', 'passed': False}
    owner_session = HttpSession(base_url)
    variant_id = discover_variant_id(owner_session)
    check['variant_id'] = variant_id

    if not variant_id:
        findings.append(
            {
                'id': 'idor_setup_failed_variant',
                'severity': 'high',
                'message': 'No se encontro variante con stock para prueba IDOR.',
            }
        )
        check['details'] = 'No hay variante disponible.'
        return check, findings

    csrf_token = owner_session.ensure_csrf('/')
    add_response = owner_session.request(
        'POST',
        '/api/cart/items/',
        json_data={'variant_id': variant_id, 'quantity': 1},
        headers={
            'X-CSRFToken': csrf_token,
            'Referer': urljoin(base_url.rstrip('/') + '/', ''),
        },
    )
    check['add_to_cart_status'] = add_response.status_code
    if add_response.status_code != 201:
        findings.append(
            {
                'id': 'idor_setup_failed_add_to_cart',
                'severity': 'high',
                'message': f'No se pudo preparar carrito para IDOR (status {add_response.status_code}).',
            }
        )
        check['details'] = 'No se pudo agregar producto al carrito.'
        return check, findings

    checkout_csrf = owner_session.ensure_csrf('/checkout/')
    checkout_payload = {
        'full_name': 'IDOR QA',
        'email': f'idor-{int(time.time())}@example.com',
        'phone': '',
        'line1': 'Calle QA 10',
        'city': 'Bogota',
        'state': 'DC',
        'coupon_code': '',
        'payment_method': 'whatsapp',
    }
    checkout_response = owner_session.request(
        'POST',
        '/checkout/api/checkout/confirm/',
        json_data=checkout_payload,
        headers={
            'X-CSRFToken': checkout_csrf,
            'Referer': urljoin(base_url.rstrip('/') + '/', 'checkout/'),
        },
    )
    check['checkout_status'] = checkout_response.status_code
    checkout_json = _safe_json_loads(checkout_response.body) or {}
    confirmation_url = checkout_json.get('confirmation_url')
    check['confirmation_url'] = confirmation_url

    if checkout_response.status_code != 201 or not confirmation_url:
        findings.append(
            {
                'id': 'idor_setup_failed_checkout',
                'severity': 'high',
                'message': f'No se pudo crear orden para prueba IDOR (status {checkout_response.status_code}).',
            }
        )
        check['details'] = 'No se obtuvo URL de confirmacion.'
        return check, findings

    confirmation_path = _extract_path_from_confirmation_url(confirmation_url)
    owner_confirmation = owner_session.request('GET', confirmation_path)
    attacker_session = HttpSession(base_url)
    attacker_confirmation = attacker_session.request('GET', confirmation_path)

    check['owner_confirmation_status'] = owner_confirmation.status_code
    check['attacker_confirmation_status'] = attacker_confirmation.status_code

    if owner_confirmation.status_code != 200:
        findings.append(
            {
                'id': 'idor_owner_access_failed',
                'severity': 'high',
                'message': f'La sesion legitima no pudo abrir confirmacion (status {owner_confirmation.status_code}).',
            }
        )
        check['details'] = 'Sesion propietaria no pudo acceder.'
        return check, findings

    if attacker_confirmation.status_code == 404:
        check['passed'] = True
        check['details'] = 'IDOR bloqueado correctamente para sesion ajena.'
    else:
        findings.append(
            {
                'id': 'idor_confirmation_exposed',
                'severity': 'critical',
                'message': (
                    'Sesion ajena pudo acceder a confirmacion de orden '
                    f'(status {attacker_confirmation.status_code}).'
                ),
            }
        )
        check['details'] = 'Posible IDOR en confirmacion de orden.'
    return check, findings


def main():
    parser = argparse.ArgumentParser(description='DAST checks for auth, CSRF and IDOR controls.')
    parser.add_argument('--base-url', required=True, help='Example: http://127.0.0.1:8013')
    parser.add_argument('--out', required=True, help='JSON output path')
    parser.add_argument('--failure-limit', type=int, default=8, help='Expected lockout failure limit')
    parser.add_argument(
        '--scope',
        choices=['web', 'full'],
        default='web',
        help='web=storefront/checkout checks, full=web + lockout admin',
    )
    args = parser.parse_args()

    checks = []
    findings = []

    cart_csrf_check, cart_csrf_findings = check_cart_csrf(args.base_url)
    checks.append(cart_csrf_check)
    findings.extend(cart_csrf_findings)

    checkout_csrf_check, checkout_csrf_findings = check_checkout_csrf(args.base_url)
    checks.append(checkout_csrf_check)
    findings.extend(checkout_csrf_findings)

    if args.scope == 'full':
        lockout_check, lockout_findings = check_admin_bruteforce_lockout(args.base_url, args.failure_limit)
        checks.append(lockout_check)
        findings.extend(lockout_findings)

    idor_check, idor_findings = check_confirmation_idor(args.base_url)
    checks.append(idor_check)
    findings.extend(idor_findings)

    summary = _severity_counts(findings)
    summary['total_checks'] = len(checks)
    summary['passed_checks'] = sum(1 for check in checks if check.get('passed'))

    report = {
        'tool': 'dast_auth_csrf',
        'scope': args.scope,
        'base_url': args.base_url,
        'checks': checks,
        'findings': findings,
        'summary': summary,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

    print(
        f"DAST auth/csrf -> critical={summary['critical']} high={summary['high']} "
        f"medium={summary['medium']} low={summary['low']} "
        f"passed_checks={summary['passed_checks']}/{summary['total_checks']}"
    )


if __name__ == '__main__':
    main()
