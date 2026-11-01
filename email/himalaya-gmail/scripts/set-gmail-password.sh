#!/bin/bash
# Rotate the Gmail app password in macOS Keychain.
#
# Run this in the USER'S OWN terminal, never through an agent tool: the password
# is read with `read -s` (no echo, no argv, no shell history) and piped to
# `security -i`, so it never appears in a transcript or process list.
#
# Usage: scripts/set-gmail-password.sh [keyring-entry]
#        keyring-entry defaults to himalaya-gmail (the account attribute himalaya reads)
set -euo pipefail

ENTRY="${1:-himalaya-gmail}"

printf 'New Gmail app password for %s (input hidden): ' "$ENTRY"
IFS= read -r -s PW
echo

if [ -z "${PW}" ]; then
  echo "empty password, aborted" >&2
  exit 1
fi

# -U overwrites the existing item, so rotation never leaves two valid secrets.
printf 'add-generic-password -a "%s" -s "%s" -w "%s" -U\n' "$ENTRY" "$ENTRY" "$PW" | security -i
unset PW

echo "Keychain updated. Verifying against Gmail..."
himalaya account check
