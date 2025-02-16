#!/bin/bash
echo "Running static analysis..."

# Run Checkstyle for Java projects
if command -v checkstyle &> /dev/null; then
  checkstyle -c /google_checks.xml src/ || echo "Checkstyle found issues."
else
  echo "❌ Checkstyle is not installed."
fi

# Run Semgrep for security analysis
if command -v semgrep &> /dev/null; then
  semgrep --config=auto . || echo "Semgrep found issues."
else
  echo "❌ Semgrep is not installed."
fi

echo "✅ Static analysis completed!"
