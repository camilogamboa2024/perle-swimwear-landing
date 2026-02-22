#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate stress gate for Perle QA run.')
    parser.add_argument('--input', required=True, help='Path to stress_all.json')
    parser.add_argument('--stock-cap', type=int, required=True, help='Expected max successful checkouts.')
    return parser.parse_args()


def main():
    args = parse_args()
    payload = json.loads(Path(args.input).read_text(encoding='utf-8'))

    cart_5xx = int(payload.get('cart_stress', {}).get('server_5xx', 0))
    checkout_5xx = int(payload.get('checkout_race', {}).get('checkout_5xx', 0))
    checkout_success = int(payload.get('checkout_race', {}).get('checkout_success_201', 0))
    stock_final = int(payload.get('stock_final', 0))

    violations = []
    if cart_5xx != 0:
        violations.append(f'cart_5xx={cart_5xx} (esperado 0)')
    if checkout_5xx != 0:
        violations.append(f'checkout_5xx={checkout_5xx} (esperado 0)')
    if stock_final < 0:
        violations.append(f'stock_final={stock_final} (esperado >= 0)')
    if checkout_success > args.stock_cap:
        violations.append(
            f'checkout_success_201={checkout_success} excede stock_cap={args.stock_cap}'
        )

    report = {
        'passed': not violations,
        'violations': violations,
        'observed': {
            'cart_5xx': cart_5xx,
            'checkout_5xx': checkout_5xx,
            'checkout_success_201': checkout_success,
            'stock_final': stock_final,
            'stock_cap': args.stock_cap,
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=True))

    if violations:
        sys.exit(1)


if __name__ == '__main__':
    main()
