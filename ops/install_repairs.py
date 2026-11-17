#!/usr/bin/env python3
"""Install into the existing Muse VM. Never places calls, sends mail or pays.

Default is a read-only provider preview. --apply installs helper files and
updates the four existing assistants, preserving their current models/voices.
The lookup server is copied but an already-running old process is not killed.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    vault=Path("/opt/muse/skills/custom-connector-setup/bin/dynamic_credentials.py")
    if not vault.is_file():
        print(json.dumps({"ok":False,"error":"authorized_muse_runtime_required","changed":False}))
        return 1
    helper=ROOT/"connectors/custom.vapi/bin/vapi.py"
    preview=subprocess.run([sys.executable,str(helper),"repair-assistants"],capture_output=True,text=True)
    if preview.returncode:
        print(preview.stdout)
        return 1
    if not args.apply:
        print(preview.stdout)
        print("Preview only. --apply installs code and updates saved assistant configuration; no calls or messages.")
        return 0
    subprocess.run([sys.executable,"-m","unittest","discover","-s",str(ROOT/"tests")],cwd=ROOT,check=True)
    targets={
        "connectors/custom.vapi/bin/vapi.py":Path.home()/"workspace/custom-connectors/custom.vapi/bin/vapi.py",
        "connectors/custom.vapi/bin/call_runtime.py":Path.home()/"workspace/custom-connectors/custom.vapi/bin/call_runtime.py",
        "connectors/custom.vapi/bin/checkout.py":Path.home()/"workspace/custom-connectors/custom.vapi/bin/checkout.py",
        "jarvis/server.py":Path.home()/"workspace/jarvis-brain/server.py",
        "jarvis/stack_watchdog.py":Path.home()/"workspace/jarvis-brain/stack_watchdog.py",
    }
    backup=Path.home()/".local/state/booked-solid/backups"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup.mkdir(parents=True,mode=0o700)
    for relative,target in targets.items():
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.is_file():
            saved=backup/relative
            saved.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            shutil.copy2(target,saved)
            os.chmod(saved,0o600)
        fd,temp=tempfile.mkstemp(dir=target.parent,prefix="repair-")
        try:
            with os.fdopen(fd,"wb") as out:out.write((ROOT/relative).read_bytes())
            os.chmod(temp,0o700)
            os.replace(temp,target)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    result=subprocess.run([sys.executable,str(targets["connectors/custom.vapi/bin/vapi.py"]),"repair-assistants","--apply"],capture_output=True,text=True)
    print(result.stdout)
    print(json.dumps({"source_helpers_installed":True,"assistant_update_verified":result.returncode==0,
        "calls_placed":0,"emails_sent":0,"sms_added":False,
        "remaining":["Install/sync the checkout-delivery Muse task and updated wave instructions using Muse's scheduler.",
                     "Verify the live Stripe link and charges before enabling checkout handoffs.",
                     "Restart only the known lookup server when calls are idle, then run stack_watchdog.py and require HEALTHY.",
                     "Run a separately authorized real call and inspect actual provider receipts; offline tests are not live proof."]}))
    return result.returncode


if __name__=="__main__":
    sys.exit(main())
