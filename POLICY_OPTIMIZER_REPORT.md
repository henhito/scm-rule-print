# Policy Optimizer report export

Read-only companion script: `policy-optimizer-report.py`.

## Run

```bash
python3 -m pip install requests
export SCM_ACCESS_TOKEN="paste-short-lived-token-here"
python3 policy-optimizer-report.py --manager cloud_managed --details
```

Safer token entry on macOS zsh (avoids shell history):

```bash
read -s "SCM_ACCESS_TOKEN?Token: "
export SCM_ACCESS_TOKEN
echo
python3 policy-optimizer-report.py --manager cloud_managed --details
```

Alternatively, omit `SCM_ACCESS_TOKEN` and supply an untracked local `secrets.json` containing `SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, and `SCM_TSG_ID`.

## Files

- `policy_optimizer_YYYYMMDD_HHMMSS.csv`: flat rule summary, for Excel or printing.
- `policy_optimizer_YYYYMMDD_HHMMSS.json`: original response objects, with optional `_optimizer_detail` information. This retains fields not anticipated in the CSV.

Without `--details`, only the listing is retrieved. With `--details`, the script requests each rule's optimization recommendations.

## Constraints

- This API lists **only rules with optimization recommendations**, not all SCM security rules.
- The API does not promise Panorama-equivalent hit counters, first/last hit or audit timestamps. CSV columns for those values stay empty unless the returned payload explicitly contains them.
- `403 AUTHZ_DENIED` means the OAuth service account lacks access to this API. The existing View Only Admin account has already returned 403; confirm entitlement/role with your PANW administrator or support. This script does not work around permissions.
- No live API test was performed. Query/filter/response details should be validated against your tenant. Unexpected response data causes an error rather than an invented report.
- Protect the raw JSON because rule configuration can be sensitive. Do not commit credentials or report output to a public repository.

References: https://pan.dev/scm/api/config/posture-management/policy-optimizer/list-policy-optimizer-security-rules/ and https://pan.dev/scm/api/config/posture-management/policy-optimizer/get-policy-optimizer-security-rules-by-id/
