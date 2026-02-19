## Summary
- Phase 0 baseline:
- Phase 1 UI/UX:
- Phase 2 Admin:
- Phase 3 QA:
- Phase 4 Security/CI:
- Phase 5 Docs:

## Verification Commands
```bash
cd ecommerce_perle
python manage.py check
DEBUG=0 DJANGO_SECRET_KEY='long-secret-50-plus-characters' ALLOWED_HOSTS='perle-ecommerce.onrender.com' CSRF_TRUSTED_ORIGINS='https://perle-ecommerce.onrender.com' DATABASE_URL='sqlite:///db.sqlite3' python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
ruff check .
bandit -q -r apps core -lll
pip-audit -r requirements.txt
npm install
npx playwright test --project=chromium
```

## Manual QA Checklist
- [ ] Home premium responsive
- [ ] Product detail variants/stock
- [ ] Cart stepper/update/remove/clear
- [ ] Checkout success + error states
- [ ] Confirmation session guard
- [ ] WhatsApp optional behavior
- [ ] Admin dashboard KPIs
- [ ] Admin mass actions and inventory adjustments

## Deployment Notes
- [ ] Render env vars verified
- [ ] Migrations applied
- [ ] Static files collected

## Backward Compatibility / Breaking Changes
- Order statuses now include `shipped` and `delivered`.
- Invalid/expired coupon now blocks checkout with `400` and `code=invalid_coupon`.
