"""Read-only SCM Policy Optimizer report exporter (CSV + JSON)."""
import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://api.strata.paloaltonetworks.com/posture/v1/policy-optimizer/security-rules"
AUTH = "https://auth.apps.paloaltonetworks.com/oauth2/access_token"


def get_token():
    token = os.getenv("SCM_ACCESS_TOKEN", "").strip()
    if token:
        return token
    config = Path("secrets.json")
    if not config.is_file():
        raise RuntimeError("Set SCM_ACCESS_TOKEN, or provide a local secrets.json")
    settings = json.loads(config.read_text(encoding="utf-8"))
    for field in ("SCM_CLIENT_ID", "SCM_CLIENT_SECRET", "SCM_TSG_ID"):
        if not settings.get(field):
            raise RuntimeError(f"Missing {field} in secrets.json")
    response = requests.post(
        AUTH,
        auth=(settings["SCM_CLIENT_ID"], settings["SCM_CLIENT_SECRET"]),
        data={"grant_type": "client_credentials", "scope": f"tsg_id:{settings['SCM_TSG_ID']}"},
        timeout=30,
    )
    check(response)
    return response.json()["access_token"]


def check(response):
    if response.status_code == 403:
        raise RuntimeError(
            "HTTP 403 AUTHZ_DENIED: this OAuth service account is not authorised "
            "for Policy Optimizer. Review Posture API roles/entitlements; "
            "SCM configuration read access alone is insufficient."
        )
    if not response.ok:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:1000]}")


def get_json(session, url, params):
    response = session.get(url, params=params, timeout=60)
    check(response)
    return response.json()


def unwrap(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected response format: expected JSON object or list")
    data = payload.get("data", [])
    if isinstance(data, dict):
        return data.get("items", data.get("results", []))
    return data


def choose(rule, *keys):
    for key in keys:
        value = rule.get(key)
        if value is not None and value != "":
            return value
    return ""


def flat(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value) if value is not None else ""


def fetch_rules(session, manager, limit):
    all_rules = []
    offset = 0
    while True:
        payload = get_json(session, BASE, {
            "manager_hostname": manager, "limit": limit, "offset": offset
        })
        batch = unwrap(payload)
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected data type in paginated response")
        all_rules.extend(batch)
        total = payload.get("total") if isinstance(payload, dict) else None
        if not batch or len(batch) < limit or (total is not None and len(all_rules) >= int(total)):
            break
        offset += len(batch)
    return all_rules


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manager", default="cloud_managed", help="cloud_managed or Panorama hostname")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--details", action="store_true", help="Retrieve each rule's full recommendations")
    parser.add_argument("--output", default=".", help="Output folder")
    args = parser.parse_args()
    if not 1 <= args.limit <= 200:
        parser.error("--limit must be between 1 and 200")
    try:
        session = requests.Session()
        session.headers.update({
            "Authorization": "Bearer " + get_token(),
            "Accept": "application/json",
        })
        rules = fetch_rules(session, args.manager, args.limit)
        if args.details:
            for i, rule in enumerate(rules, start=1):
                rule_id = choose(rule, "id", "rule_id", "uuid")
                if rule_id:
                    # Keep full detail in JSON, including recommendation structures.
                    rule["_optimizer_detail"] = get_json(
                        session, f"{BASE}/{rule_id}", {"manager_hostname": args.manager}
                    )
                print(f"Fetched details: {i}/{len(rules)}", end="\r", file=sys.stderr)
            print(file=sys.stderr)
        columns = [
            "ID", "Name", "Location", "Status", "Action", "Application",
            "Hit Count (if provided)", "First Hit (if provided)",
            "Last Hit (if provided)", "Created (if provided)",
            "Modified (if provided)", "Recommendations (JSON)",
        ]
        rows = []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            detail = rule.get("_optimizer_detail", {})
            recs = (detail.get("recommended_rules", [])
                    if isinstance(detail, dict) else [])
            rows.append([
                flat(choose(rule, "id", "rule_id", "uuid")),
                flat(choose(rule, "name", "rule_name")),
                flat(choose(rule, "location", "folder", "device_group", "snippet")),
                flat(choose(rule, "status", "optimization_status")),
                flat(choose(rule, "action")),
                flat(choose(rule, "application", "applications")),
                flat(choose(rule, "hit_count", "rule_hit_count")),
                flat(choose(rule, "first_hit_timestamp", "first_hit")),
                flat(choose(rule, "last_hit_timestamp", "last_hit")),
                flat(choose(rule, "created_at", "created")),
                flat(choose(rule, "modified_at", "updated_at", "last_modified")),
                flat(recs),
            ])
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        stem = f"policy_optimizer_{timestamp}"
        csv_file, json_file = output / f"{stem}.csv", output / f"{stem}.json"
        with csv_file.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
        json_file.write_text(json.dumps({
            "manager": args.manager,
            "exported_at_utc": datetime.now(timezone.utc).isoformat(),
            "rule_count": len(rules),
            "rules": rules,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Policy Optimizer rules with recommendations: {len(rules)}")
        print("Note: this is NOT a complete security policy or a Panorama hit-count report.")
        print(f"CSV: {csv_file}")
        print(f"JSON: {json_file}")
        for row in rows[:20]:
            print(f"  {row[1] or '(unnamed)'} | {row[2]} | {row[3]}")
    except (requests.RequestException, ValueError, KeyError, RuntimeError) as e:
        print(f"Report failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
