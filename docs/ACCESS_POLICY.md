# MarineCatch Africa — Access Policy

## Principle
Access is granted based on role and need.
No shared passwords. No shared accounts.
Every person has their own credentials.

## Access Levels

### Level 1 — Production (Founder only)
- AWS root account
- Production database
- M-Pesa production credentials
- WhatsApp Business account owner
- Domain registrar (Namecheap)
- All financial accounts

### Level 2 — Leadership (CTO + CIO)
- GitHub full access
- AWS IAM accounts (defined permissions)
- Staging database
- Production read access (audit only)
- Architecture decisions

### Level 3 — Development (Engineers)
- GitHub collaborator access
- Development database only
- Sandbox credentials only
- No production access

### Level 4 — Operations (Sales, Marketing)
- Dashboard access only
- No code repository access
- No database access
- No API credentials

## Rules
1. Never share passwords via WhatsApp or email
2. Use .env.example — never real .env files
3. Every person signs contributor agreement
4. Production changes require founder approval
5. All credentials stored in password manager

## Credential Management
Production credentials: Founder only
Development credentials: Available in .env.example
Sandbox API keys: Each developer gets their own