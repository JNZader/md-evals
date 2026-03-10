# Security Policy

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability in md-evals, please report it responsibly using one of these methods:

### Option 1: GitHub Security Advisory (Recommended)

1. Go to the [Security tab](https://github.com/JNZader/md-evals/security)
2. Click "Report a vulnerability"
3. Fill in the security advisory form with details

This keeps the vulnerability private until we can address it.

### Option 2: Email

Send a detailed report to:

**Email:** javier@example.com  
**Subject:** `[SECURITY] Vulnerability Report: [brief description]`

Include:
- Vulnerability description
- Affected version(s)
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Option 3: GPG Encrypted Email (If Needed)

If you prefer additional security, you can encrypt using GPG:

```bash
# Contact maintainer for public key
gpg --trust-model always --encrypt --recipient <key-id> message.txt
```

## What Happens Next

### Timeline

1. **Within 48 hours** - We'll acknowledge receipt of your report
2. **Within 5 days** - We'll provide an initial assessment
3. **Within 30 days** - We'll have a fix ready or timeline for fix
4. **Coordinated disclosure** - We'll work with you on release timing

### Our Commitment

We commit to:

✅ **Treat all security reports seriously**  
✅ **Maintain confidentiality** of reporters  
✅ **Respond promptly** to inquiries  
✅ **Fix vulnerabilities** in timely manner  
✅ **Provide credit** (unless you prefer anonymity)  
✅ **Keep you informed** throughout the process  

## Security Practices

### Current Practices

- **Dependencies**: Pinned versions in pyproject.toml
- **Testing**: Comprehensive pytest coverage
- **Code Review**: All PRs reviewed before merge
- **Type Hints**: Full type annotations for safety
- **Validation**: Input validation using Pydantic

### What We Monitor

- **Dependencies**: Updates and vulnerability advisories
- **Code Quality**: Static analysis and linting
- **Access Control**: GitHub repository settings
- **Secrets**: No API keys or tokens in code

### Known Limitations

Be aware of these limitations when using md-evals:

⚠️ **API Keys**: Store API keys in environment variables, not config files  
⚠️ **Network**: Uses HTTPS for all API calls  
⚠️ **YAML Parsing**: Ensure eval.yaml comes from trusted sources  
⚠️ **Model Output**: LLM responses are untrusted third-party content  

## Supported Versions

| Version | Status | Security Updates |
|---------|--------|------------------|
| 1.0.0+ | Current | ✅ Actively supported |
| < 1.0.0 | Obsolete | ❌ Not supported |

## Security Updates

When security vulnerabilities are fixed:

1. **Patch release** is published (e.g., 1.0.1)
2. **Security advisory** is published on GitHub
3. **CHANGELOG** documents the fix
4. **Dependencies** are updated if needed

### Receiving Updates

To stay informed about security updates:

- 👀 Watch the repository for releases
- ⭐ Star the project on GitHub
- 📧 Follow security advisories

## Vulnerability Disclosure Timeline

### Public Disclosure Date

Vulnerabilities will be publicly disclosed:
- When a patch is released
- After 90 days if no patch exists
- At reporter's request (with patch available)

### Coordinated Disclosure

We ask reporters to:
- Keep details confidential until patch is released
- Allow time for users to update
- Avoid public discussion of unreleased vulnerabilities

### Breaking Embargo

Embargo can be broken if:
- The vulnerability is publicly disclosed elsewhere
- Active exploitation is detected in the wild
- 90 days have passed since initial report

## Security Dependencies

### Direct Dependencies

Key dependencies and how we manage them:

- **litellm** - LLM provider abstraction
  - Version: Pinned, updated regularly
  - Security: Uses HTTPS for all APIs
  
- **pydantic** - Data validation
  - Version: Latest minor version
  - Security: Well-maintained, security-focused project
  
- **typer** - CLI framework
  - Version: Pinned to stable releases
  - Security: Minimal security surface
  
- **pyyaml** - YAML parsing
  - Version: Latest with safe loader
  - Security: Never uses unsafe_load()

See [pyproject.toml](pyproject.toml) for full dependency list.

### Vulnerability Monitoring

We monitor for vulnerabilities using:
- GitHub Dependabot
- Security advisories
- Community reports

## Best Practices for Users

### When Using md-evals

1. **Protect API Keys**
   ```bash
   # ✅ DO: Use environment variables
   export GITHUB_TOKEN="your-token"
   
   # ❌ DON'T: Commit to version control
   # ❌ DON'T: Include in eval.yaml
   ```

2. **Validate Configuration**
   - Review eval.yaml before running
   - Trust only configuration from known sources
   - Use version control for configuration

3. **Keep Updated**
   ```bash
   # Check for updates
   pip list --outdated
   
   # Update md-evals
   pip install --upgrade md-evals
   ```

4. **Report Suspicions**
   - If you suspect a breach or exploitation
   - Contact security team immediately
   - Do not share details publicly first

## Responsible Disclosure

We appreciate security researchers following responsible disclosure:

✅ **Do**:
- Report privately first
- Give us time to fix
- Be detailed in reports
- Use clear communication
- Follow up appropriately

❌ **Don't**:
- Publicly disclose before fix
- Exploit beyond proof-of-concept
- Demand compensation
- Share details prematurely
- Be hostile or threatening

## Legal Considerations

### No Bounty Program

md-evals does not currently have a bug bounty program. However:
- We deeply appreciate security research
- Reporters receive credit in advisories
- We follow coordinated disclosure practices
- Your contribution strengthens the project

### Safe Harbor

To encourage responsible disclosure:
- We won't pursue legal action for good-faith reporting
- We won't share reporter information
- We protect researchers' privacy

## Questions or Concerns?

For security-related questions:

📧 **Email**: javier@example.com  
**Subject**: `[SECURITY] Question: [topic]`

For other questions:
- 💬 [GitHub Discussions](https://github.com/JNZader/md-evals/discussions)
- 📚 [Documentation](https://jnzader.github.io/md-evals/)

## Security Advisory History

### Recent Advisories

No security vulnerabilities have been reported yet.

See [GitHub Security Advisories](https://github.com/JNZader/md-evals/security/advisories) for complete history.

## Related Documents

- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Community standards
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [CHANGELOG.md](CHANGELOG.md) - Release information
- [LICENSE](LICENSE) - MIT License

---

Thank you for helping keep md-evals secure! 🛡️
