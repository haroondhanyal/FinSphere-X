#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if rg -n 'JWT_SECRET\s*=\s*["\x27][^$<][^"\x27]{20,}' --glob '!README.md' --glob '!docs/**' --glob '!*.lock' --glob '!scripts/security-check.sh' .; then
  echo "Possible committed JWT secret found" >&2
  exit 1
fi

if rg -n 'password\s*[:=]\s*["\x27](?!(?:FinSphere-Demo-2026!|admin12345678)["\x27])[^"\x27]{8,}' --pcre2 apps/api/app apps/web/src; then
  echo "Possible hard-coded password found in application source" >&2
  exit 1
fi

echo "Source secret-pattern checks passed"
