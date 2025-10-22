# Docker Build & Security Scanning Workflow

This document describes the automated Docker build and security scanning workflow for the 7monthIndicator trading bot system.

## Overview

The `docker-security.yml` workflow provides comprehensive Docker image building, testing, and security vulnerability scanning using Trivy. It runs automatically on code changes and weekly for continuous security monitoring.

## Workflow Triggers

The workflow runs on:
- **Push events** to `main`, `develop`, or `binance` branches when Docker-related files change
- **Pull requests** to `main` or `develop` branches
- **Manual trigger** via GitHub Actions UI (workflow_dispatch)
- **Weekly schedule** every Monday at 00:00 UTC for security updates

## Jobs

### 1. Docker Build & Test (`docker-build-test`)

Builds and tests Docker images for all services in parallel.

**Services tested:**
- `rl-bot` - Reinforcement Learning trading bot
- `chart-bot` - Chart analysis service
- `crewai-bot` - Multi-agent AI system
- `web-dashboard` - Web interface

**What it does:**
- Sets up Docker Buildx for efficient multi-platform builds
- Caches Docker layers to speed up builds
- Extracts metadata and generates proper tags
- Builds each service from the Dockerfile
- Tests image functionality (Python version, basic health checks)
- Saves built images as artifacts for security scanning
- Reports image size and metadata

**Outputs:**
- Docker image artifacts for each service
- Build logs and metadata
- Image size reports

### 2. Trivy Security Scan (`trivy-security-scan`)

Scans each Docker image for security vulnerabilities using Aqua Security's Trivy.

**Vulnerability Types Detected:**
- Operating system vulnerabilities
- Library and package vulnerabilities
- Known CVEs (Common Vulnerabilities and Exposures)

**Severity Levels:**
- 🔴 **CRITICAL** - Immediate action required
- 🟠 **HIGH** - Should be addressed soon
- 🟡 **MEDIUM** - Plan for remediation
- 🟢 **LOW** - Monitor and consider fixing

**What it does:**
- Downloads built Docker images from previous job
- Runs Trivy scanner with comprehensive vulnerability detection
- Generates SARIF format results for GitHub Security tab
- Creates human-readable table format reports
- Counts vulnerabilities by severity
- Generates detailed security summaries
- Uploads results to GitHub Security tab
- Creates artifacts with scan results

**Outputs:**
- SARIF files uploaded to GitHub Security tab
- Detailed vulnerability reports (`.txt` files)
- Security summary markdown files
- Vulnerability counts by severity

### 3. Docker Compose Stack Test (`docker-compose-test`)

Tests the complete Docker Compose stack deployment.

**What it does:**
- Creates test environment variables
- Validates `docker-compose.yml` syntax
- Builds all services with Docker Compose
- Starts the complete stack
- Waits for services to become healthy
- Tests web dashboard accessibility
- Checks service health endpoints
- Collects logs from all services

**Health Checks:**
- Web dashboard `/health` endpoint
- Main page accessibility at `http://localhost:5000/`
- Service startup and readiness

**Outputs:**
- Docker Compose logs for all services
- Individual service logs
- Health check results

### 4. Security Report (`security-report`)

Generates a comprehensive security report combining results from all services.

**What it does:**
- Downloads all Trivy scan results
- Combines security summaries from all services
- Calculates total vulnerability counts across the stack
- Generates overall security status
- Creates detailed markdown report
- Posts report to PR comments (if applicable)
- Publishes to GitHub Actions summary

**Report Includes:**
- Per-service vulnerability breakdown
- Total vulnerability counts
- Severity distribution
- Actionable recommendations
- Scan metadata (date, commit, branch)

**Outputs:**
- `SECURITY_REPORT.md` with complete analysis
- GitHub Actions job summary
- PR comments (for pull requests)

## Using the Workflow

### Viewing Results

1. **GitHub Actions Tab:**
   - Go to your repository → Actions → "Docker Build & Security Scan"
   - Click on any workflow run to see detailed results

2. **GitHub Security Tab:**
   - Go to repository → Security → Code scanning alerts
   - Filter by "trivy-" categories to see vulnerabilities by service

3. **Workflow Artifacts:**
   - Download artifacts from workflow runs:
     - Docker images (7-day retention)
     - Trivy scan results (30-day retention)
     - Security reports (90-day retention)
     - Docker Compose logs (7-day retention)

### Manual Trigger

To run the workflow manually:

1. Go to Actions → "Docker Build & Security Scan"
2. Click "Run workflow"
3. Select branch
4. Click "Run workflow" button

### Understanding Results

**All Clear:**
```
✅ No critical or high severity vulnerabilities detected!
```

**Attention Needed:**
```
⚠️ High severity vulnerabilities detected. Please review and plan remediation.
```

**Critical Issues:**
```
🚨 Action Required: Critical vulnerabilities detected. Please review and remediate immediately.
```

## Responding to Security Findings

### When Vulnerabilities are Found:

1. **Review the Report:**
   - Check the security summary in the workflow run
   - Review detailed vulnerability information in Trivy reports
   - Identify affected packages and versions

2. **Assess Impact:**
   - Determine if the vulnerability affects your usage
   - Check if updates are available
   - Review CVE details and severity justification

3. **Remediate:**
   - Update affected packages in `requirements.txt`
   - Rebuild Docker images
   - Re-run security scan to verify fixes
   - Consider using alternative packages if updates aren't available

4. **Document:**
   - If accepting risk, document why in the PR/commit
   - Track remediation in issues if immediate fix isn't possible

### Common Remediation Steps:

**Python Package Vulnerabilities:**
```bash
# Update specific package
pip install --upgrade <package-name>

# Update requirements.txt
pip freeze > requirements.txt

# Test changes
./quick_test.sh
```

**Base Image Vulnerabilities:**
```dockerfile
# Update base image in Dockerfile
FROM python:3.11-slim  # Use latest patch version
```

## Performance Optimizations

The workflow includes several optimizations:

1. **Docker Layer Caching:**
   - Caches layers between runs
   - Significantly speeds up builds

2. **Parallel Execution:**
   - Builds all services in parallel
   - Runs security scans concurrently

3. **Artifact Sharing:**
   - Shares built images between jobs
   - Avoids redundant builds

4. **Conditional Execution:**
   - Only runs on relevant file changes
   - Skips unnecessary scans

## Troubleshooting

### Build Failures

**Issue:** Docker build fails
```
Solution: Check Dockerfile syntax and dependencies in requirements.txt
```

**Issue:** Out of disk space
```
Solution: Workflow includes cleanup steps, but check runner capacity
```

### Scan Failures

**Issue:** Trivy timeout
```
Solution: Timeout is set to 15 minutes. Large images may need adjustment.
```

**Issue:** SARIF upload fails
```
Solution: Check repository permissions for security events
```

### Stack Test Failures

**Issue:** Services won't start
```
Solution: Check .env file configuration and service dependencies
```

**Issue:** Health checks fail
```
Solution: Verify web dashboard health endpoint and service readiness
```

## Customization

### Adjusting Scan Severity

Edit the workflow to change severity levels:

```yaml
severity: 'CRITICAL,HIGH'  # Only scan for critical and high
```

### Changing Scan Schedule

Modify the cron schedule:

```yaml
schedule:
  - cron: '0 0 * * 1'  # Weekly on Monday
  - cron: '0 0 * * *'  # Daily at midnight
```

### Adding New Services

To add a new service to the scan:

1. Add to the matrix in `docker-build-test`:
```yaml
matrix:
  service: [rl-bot, chart-bot, crewai-bot, web-dashboard, new-service]
```

2. Ensure the Dockerfile has a target for the new service

3. Update docker-compose.yml if needed

## Best Practices

1. **Review Security Reports Regularly:**
   - Check weekly scan results
   - Monitor security tab for new alerts
   - Prioritize critical and high severity issues

2. **Keep Dependencies Updated:**
   - Regularly update `requirements.txt`
   - Use dependabot or similar tools
   - Test updates before deploying

3. **Monitor Build Times:**
   - Review workflow duration
   - Optimize Docker layers if builds are slow
   - Consider splitting large services

4. **Document Accepted Risks:**
   - If choosing not to fix a vulnerability, document why
   - Review accepted risks periodically
   - Re-evaluate when circumstances change

## Integration with CI/CD

This workflow integrates with your existing CI/CD:

- Runs before deployment
- Provides security gates
- Integrates with GitHub Security features
- Generates actionable reports

## Support and Resources

- **Trivy Documentation:** https://aquasecurity.github.io/trivy/
- **GitHub Security:** https://docs.github.com/en/code-security
- **Docker Best Practices:** https://docs.docker.com/develop/dev-best-practices/

---

*This workflow is part of the 7monthIndicator trading bot security infrastructure.*
