#!/usr/bin/env python3
import argparse
import concurrent.futures
import http.cookiejar
import json
import math
import random
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def now_ms():
    return int(time.time() * 1000)


def percentile(values, p):
    if not values:
        return 0.0
    sorted_values = sorted(values)
    idx = max(0, min(len(sorted_values) - 1, math.ceil((p / 100.0) * len(sorted_values)) - 1))
    return float(sorted_values[idx])


class HttpSession:
    def __init__(self, base_url, timeout=20):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.cookiejar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))

    def cookie(self, name):
        for cookie in self.cookiejar:
            if cookie.name == name:
                return cookie.value
        return ''

    def request(self, method, path, *, json_body=None, form_body=None, headers=None):
        url = f'{self.base_url}{path}'
        data = None
        request_headers = dict(headers or {})

        if json_body is not None:
            data = json.dumps(json_body).encode('utf-8')
            request_headers.setdefault('Content-Type', 'application/json')
        elif form_body is not None:
            data = urllib.parse.urlencode(form_body).encode('utf-8')
            request_headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')

        request = urllib.request.Request(url, data=data, method=method, headers=request_headers)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                status = response.status
                text = response.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as exc:
            status = exc.code
            text = exc.read().decode('utf-8', 'replace')

        payload = None
        try:
            payload = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            payload = None

        return {
            'status': status,
            'text': text,
            'json': payload,
        }


def fetch_products(base_url):
    session = HttpSession(base_url)
    response = session.request('GET', '/api/products/')
    if response['status'] != 200 or not isinstance(response['json'], list) or not response['json']:
        raise RuntimeError('No se pudieron cargar productos desde /api/products/.')
    return response['json']


def first_variant_id(products):
    for product in products:
        variants = product.get('variants') or []
        if variants:
            return variants[0].get('id')
    return None


def variant_stock(products, variant_id):
    for product in products:
        for variant in product.get('variants') or []:
            if variant.get('id') == variant_id:
                return int(variant.get('stock') or 0)
    return None


def cart_worker(idx, base_url, variant_id, iterations):
    session = HttpSession(base_url)
    stats = {
        'worker': idx,
        'ops': 0,
        'server_5xx': 0,
        'json_errors': 0,
        'negative_qty_hits': 0,
        'status_counts': {},
        'exceptions': 0,
    }
    item_id = None

    try:
        home = session.request('GET', '/')
        if home['status'] >= 500:
            stats['server_5xx'] += 1
        csrf_token = session.cookie('csrftoken')
    except Exception:
        stats['exceptions'] += 1
        return stats

    for i in range(iterations):
        op = i % 4
        headers = {
            'X-CSRFToken': csrf_token,
            'Referer': f'{base_url}/',
        }

        try:
            if op == 0:
                response = session.request(
                    'POST',
                    '/api/cart/items/',
                    json_body={'variant_id': variant_id, 'quantity': 1},
                    headers=headers,
                )
            elif op == 1:
                if item_id is None:
                    response = session.request(
                        'POST',
                        '/api/cart/items/',
                        json_body={'variant_id': variant_id, 'quantity': 1},
                        headers=headers,
                    )
                else:
                    response = session.request(
                        'PATCH',
                        f'/api/cart/items/{item_id}/',
                        json_body={'quantity': random.choice([1, 2, 3])},
                        headers=headers,
                    )
            elif op == 2:
                if item_id is None:
                    response = session.request('GET', '/api/cart/')
                else:
                    response = session.request(
                        'DELETE',
                        f'/api/cart/items/{item_id}/',
                        json_body={},
                        headers=headers,
                    )
                    item_id = None
            else:
                response = session.request(
                    'POST',
                    '/api/cart/clear/',
                    json_body={},
                    headers=headers,
                )
                item_id = None

            stats['ops'] += 1
            status = int(response['status'])
            key = str(status)
            stats['status_counts'][key] = stats['status_counts'].get(key, 0) + 1
            if status >= 500:
                stats['server_5xx'] += 1

            payload = response['json']
            if isinstance(payload, dict):
                items = payload.get('items') or []
                if items:
                    item_id = items[0].get('id')
                for item in items:
                    if int(item.get('quantity') or 0) < 0:
                        stats['negative_qty_hits'] += 1
            elif payload is None and status < 500:
                stats['json_errors'] += 1
        except Exception:
            stats['exceptions'] += 1

    return stats


def checkout_worker(idx, base_url, variant_id):
    session = HttpSession(base_url)
    result = {'worker': idx, 'home': None, 'add': None, 'checkout': None, 'exception': None}

    try:
        home = session.request('GET', '/')
        result['home'] = home['status']
        csrf_token = session.cookie('csrftoken')

        add = session.request(
            'POST',
            '/api/cart/items/',
            json_body={'variant_id': variant_id, 'quantity': 1},
            headers={
                'X-CSRFToken': csrf_token,
                'Referer': f'{base_url}/',
            },
        )
        result['add'] = add['status']

        checkout = session.request(
            'POST',
            '/checkout/api/checkout/confirm/',
            json_body={
                'full_name': f'Race User {idx}',
                'email': f'race-user-{idx}@example.com',
                'phone': '3001234567',
                'line1': 'Calle race 123',
                'city': 'Bogota',
                'state': 'DC',
                'payment_method': 'whatsapp',
                'coupon_code': '',
            },
            headers={
                'X-CSRFToken': csrf_token,
                'Referer': f'{base_url}/checkout/',
            },
        )
        result['checkout'] = checkout['status']
    except Exception as exc:
        result['exception'] = repr(exc)

    return result


def admin_reader_worker(idx, base_url, username, password):
    session = HttpSession(base_url)
    statuses = []
    latencies = []
    errors = 0

    def timed_request(method, path, *, form_body=None, headers=None):
        started = time.perf_counter()
        response = session.request(method, path, form_body=form_body, headers=headers)
        latencies.append((time.perf_counter() - started) * 1000.0)
        statuses.append(int(response['status']))
        return response

    try:
        timed_request('GET', '/admin/login/')
        csrf_token = session.cookie('csrftoken')
        timed_request(
            'POST',
            '/admin/login/',
            form_body={
                'username': username,
                'password': password,
                'next': '/admin/',
                'csrfmiddlewaretoken': csrf_token,
            },
            headers={'Referer': f'{base_url}/admin/login/'},
        )

        for path in (
            '/admin/',
            '/admin/orders/order/',
            '/admin/inventory/stocklevel/',
            '/admin/catalog/product/',
            '/admin/customers/customer/',
            '/admin/orders/coupon/',
        ):
            timed_request('GET', path)
    except Exception:
        errors += 1

    return {
        'worker': idx,
        'statuses': statuses,
        'latencies_ms': latencies,
        'errors': errors,
    }


def run_cart_stress(base_url, variant_id, users, iterations):
    started = now_ms()
    workers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=users) as executor:
        futures = [
            executor.submit(cart_worker, idx, base_url, variant_id, iterations)
            for idx in range(users)
        ]
        for future in concurrent.futures.as_completed(futures):
            workers.append(future.result())

    duration_ms = now_ms() - started
    summary = {
        'users': users,
        'iterations_per_user': iterations,
        'total_ops': sum(worker['ops'] for worker in workers),
        'server_5xx': sum(worker['server_5xx'] for worker in workers),
        'json_errors': sum(worker['json_errors'] for worker in workers),
        'negative_qty_hits': sum(worker['negative_qty_hits'] for worker in workers),
        'exceptions': sum(worker['exceptions'] for worker in workers),
        'duration_ms': duration_ms,
    }
    return {'summary': summary, 'workers': workers}


def run_checkout_race(base_url, variant_id, workers_count):
    started = now_ms()
    workers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers_count) as executor:
        futures = [
            executor.submit(checkout_worker, idx, base_url, variant_id)
            for idx in range(workers_count)
        ]
        for future in concurrent.futures.as_completed(futures):
            workers.append(future.result())
    duration_ms = now_ms() - started

    checkout_statuses = [row['checkout'] for row in workers if row['checkout'] is not None]
    status_counts = {}
    for status in checkout_statuses:
        key = str(status)
        status_counts[key] = status_counts.get(key, 0) + 1

    summary = {
        'workers': workers_count,
        'duration_ms': duration_ms,
        'checkout_status_counts': status_counts,
        'checkout_success_201': status_counts.get('201', 0),
        'checkout_controlled_400': status_counts.get('400', 0),
        'checkout_controlled_409': status_counts.get('409', 0),
        'checkout_throttled_429': status_counts.get('429', 0),
        'checkout_5xx': sum(count for code, count in status_counts.items() if code.startswith('5')),
        'exceptions': sum(1 for row in workers if row['exception']),
    }
    return {'summary': summary, 'workers': workers}


def run_admin_read_heavy(base_url, rounds, admin_user, admin_pass):
    started = now_ms()
    workers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(rounds, 40)) as executor:
        futures = [
            executor.submit(admin_reader_worker, idx, base_url, admin_user, admin_pass)
            for idx in range(rounds)
        ]
        for future in concurrent.futures.as_completed(futures):
            workers.append(future.result())
    duration_ms = now_ms() - started

    statuses = []
    latencies = []
    errors = 0
    for worker in workers:
        statuses.extend(worker['statuses'])
        latencies.extend(worker['latencies_ms'])
        errors += worker['errors']

    status_counts = {}
    for status in statuses:
        key = str(status)
        status_counts[key] = status_counts.get(key, 0) + 1

    summary = {
        'rounds': rounds,
        'duration_ms': duration_ms,
        'requests_observed': len(statuses),
        'status_counts': status_counts,
        'server_5xx': sum(count for code, count in status_counts.items() if code.startswith('5')),
        'errors': errors,
        'latency_ms_p50': percentile(latencies, 50),
        'latency_ms_p95': percentile(latencies, 95),
        'latency_ms_avg': statistics.mean(latencies) if latencies else 0.0,
    }
    return {'summary': summary, 'workers': workers}


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding='utf-8')


def parse_args():
    parser = argparse.ArgumentParser(description='Stress QA runner for Perle storefront + CRM/admin.')
    parser.add_argument('--base-url', required=True, help='Base URL del entorno bajo prueba.')
    parser.add_argument('--output-dir', required=True, help='Directorio de salida para evidencia JSON.')
    parser.add_argument('--admin-user', default='qa_admin')
    parser.add_argument('--admin-pass', default='AdminPass123!')
    parser.add_argument('--stock-cap', type=int, default=20)
    parser.add_argument('--cart-users', type=int, default=40)
    parser.add_argument('--cart-iterations', type=int, default=50)
    parser.add_argument('--checkout-workers', type=int, default=60)
    parser.add_argument('--admin-rounds', type=int, default=100)
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    products = fetch_products(args.base_url)
    variant_id = first_variant_id(products)
    if variant_id is None:
        raise RuntimeError('No hay variantes activas para ejecutar estrés.')
    stock_before = variant_stock(products, variant_id)

    cart = run_cart_stress(args.base_url, variant_id, args.cart_users, args.cart_iterations)
    checkout = run_checkout_race(args.base_url, variant_id, args.checkout_workers)
    admin = run_admin_read_heavy(args.base_url, args.admin_rounds, args.admin_user, args.admin_pass)

    products_after = fetch_products(args.base_url)
    stock_after = variant_stock(products_after, variant_id)

    all_summary = {
        'generated_at_epoch_ms': now_ms(),
        'base_url': args.base_url,
        'variant_id': variant_id,
        'stock_cap': args.stock_cap,
        'stock_before': stock_before,
        'stock_final': stock_after,
        'cart_stress': cart['summary'],
        'checkout_race': checkout['summary'],
        'admin_read_heavy': admin['summary'],
    }

    write_json(output_dir / 'stress_cart.json', cart)
    write_json(output_dir / 'stress_checkout.json', checkout)
    write_json(output_dir / 'stress_admin.json', admin)
    write_json(output_dir / 'stress_all.json', all_summary)

    print(json.dumps(all_summary, indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()
