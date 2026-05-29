markdown
# MarineCatch Africa — Contributor Guide

## Environment Setup

1. Clone the repository
2. Copy `.env.example` to `backend/app/.env`
3. Fill in your local development credentials
4. Never use production credentials locally

## Database Setup

Use the development database only:
DATABASE_URL=postgresql://marinecatch_dev_user:devonly123@localhost:5432/marinecatch_dev

Never connect to production database from local machine.

## Git Workflow

- Never commit directly to `main`
- Create a feature branch: `git checkout -b feature/your-feature-name`
- Push branch and open a Pull Request
- Wait for review before merging

## Branch Naming
feature/inventory-search
fix/payment-callback-error
docs/api-documentation
test/order-service-tests

## Commit Messages
feat: add inventory search by landing site
fix: resolve payment callback null pointer
docs: update README with deployment steps
test: add unit tests for fee calculation

## What NOT to Do

- Never commit `.env` files
- Never commit real API keys or passwords
- Never push directly to main
- Never share credentials over WhatsApp or email
- Never connect local code to production database

## Getting Help

Reach out via GitHub issues or team communication channels.