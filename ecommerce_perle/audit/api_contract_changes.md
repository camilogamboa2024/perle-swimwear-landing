# API Contract Changes During Audit

## Summary
No breaking route/path changes were introduced.

## Changes made
1. Error handling hardened in mutable APIs:
   - Added explicit CSRF enforcement errors (`403`) for missing/invalid CSRF token in mutable session-based endpoints.
   - Kept existing endpoint paths and payload structures.
2. Business-rule errors remain in JSON shape with `{"error": "..."}` for checkout/cart validation paths.

## Affected endpoints
- `POST /api/cart/items/`
- `PATCH /api/cart/items/<item_id>/`
- `DELETE /api/cart/items/<item_id>/`
- `POST /api/cart/clear/`
- `POST /checkout/api/checkout/confirm/`

## QA Functional Round 20260210-033002
No additional public API route/payload breaking changes were introduced in this round.
- Internal functional fix only: authenticated customer/cart linking on guest-email collision.
- Endpoint paths remained unchanged.
