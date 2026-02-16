# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainers or use [GitHub's private vulnerability reporting](https://github.com/onvoyage-ai/voyage-geo-agent/security/advisories/new)
3. Include steps to reproduce and potential impact

We will acknowledge receipt within 48 hours and aim to release a fix within 7 days for critical issues.

## Scope

- API key handling and storage
- Input validation and injection prevention
- Dependency vulnerabilities

## Best Practices for Users

- Never commit `.env` files or API keys to version control
- Use environment variables or `.env` files for all secrets
- Keep dependencies updated (`pip install --upgrade`)
- Review AI model outputs before sharing publicly
