#!/usr/bin/env python3
"""Versioned delivery validation; v1/v2 retain their original validator."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from delivery_v3 import validate_v3


def validate(contract, repo=None, require_active=False):
    if isinstance(contract,dict) and contract.get('schema_version')==3:
        return validate_v3(contract,repo,require_active)
    import validate_delivery_legacy as legacy
    return legacy.validate(contract,repo,require_active)


def __getattr__(name):
    import validate_delivery_legacy as legacy
    return getattr(legacy,name)


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('contract',type=Path); p.add_argument('--repo',type=Path); p.add_argument('--require-active',action='store_true'); a=p.parse_args()
    try:
        c=json.loads(a.contract.read_text()); errors=validate(c,a.repo,a.require_active)
    except (OSError,ValueError,TypeError) as exc:
        errors=['contract_parse_or_validation_error']
    print(json.dumps({'valid':not errors,'errors':errors,'provider_observation':False}))
    return 1 if errors else 0


if __name__=='__main__': raise SystemExit(main())
