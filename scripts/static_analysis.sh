#!/bin/bash

echo "Running static analysis..."

# Checkstyle for Java
checkstyle -c /google_checks.xml src/main/java/

# Semgrep for security scanning
semgrep scan --config=auto .

