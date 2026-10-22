#!/usr/bin/env bash
# Installs a pre-commit hook that runs scripts/check_no_data.sh. Refuses to overwrite an existing hook.
set -e
root=$(git rev-parse --show-toplevel)
hook="$root/.git/hooks/pre-commit"
if [ -e "$hook" ]; then echo "pre-commit hook already exists at $hook; add this line to it instead:"; echo "  bash Online_Education_Company/scripts/check_no_data.sh || exit 1"; exit 1; fi
printf '#!/usr/bin/env bash\ncd "$(git rev-parse --show-toplevel)" && bash Online_Education_Company/scripts/check_no_data.sh || exit 1\n' > "$hook"
chmod +x "$hook"; echo "Installed $hook"
