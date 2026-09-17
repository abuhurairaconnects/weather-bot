"""
Security & Admin Lock Verification Test.
Ensures ONLY Primary Admin (Abu Huraira: 8953572486) has administrative rights,
and tests both public access and restricted access scenarios.
"""
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    PRIMARY_ADMIN_ID,
    ADMIN_IDS,
    ONLY_ADMIN_ACCESS,
    is_admin,
    is_authorized,
    ACCESS_DENIED_MESSAGE_BN
)

def test_admin_lock():
    print("========================================")
    print("🛡️ Testing Bot Admin Whitelist Security Lock")
    print("========================================")

    print(f"Primary Admin ID: {PRIMARY_ADMIN_ID}")
    print(f"Configured Admin IDs: {ADMIN_IDS}")
    print(f"Admin Only Access Mode: {ONLY_ADMIN_ACCESS}")

    assert PRIMARY_ADMIN_ID == 8953572486, "Primary Admin ID mismatch"
    assert 8953572486 in ADMIN_IDS, "Primary Admin must be in ADMIN_IDS"

    # 1. Test Admin Privilege Check (is_admin)
    print("\n[1/3] Testing is_admin(): Developer Abu Huraira vs Strangers...")
    assert is_admin(8953572486) is True, "Abu Huraira (8953572486) MUST be admin!"
    print("  ✅ Admin access GRANTED for Abu Huraira (8953572486).")

    strangers = [123456, 987654321, 11223344, 999999999, 0, None]
    for uid in strangers:
        res = is_admin(uid)
        assert res is False, f"Stranger {uid} must NOT have admin rights!"
    print("  ✅ All strangers strictly denied admin dashboard & commands!")

    # 2. Test Authorization Mode (is_authorized)
    print("\n[2/3] Testing is_authorized(): Current mode behavior...")
    assert is_authorized(PRIMARY_ADMIN_ID) is True
    if ONLY_ADMIN_ACCESS:
        print("  🔒 Restricted Mode: Only admin is authorized.")
        for uid in strangers:
            assert is_authorized(uid) is False
    else:
        print("  🌐 Public Mode: Public can view weather while admin rights are protected.")
        assert is_authorized(123456) is True

    # 3. Test Rejection Message Integrity
    print("\n[3/3] Testing Access Denied Message...")
    assert "অ্যাক্সেস সীমাবদ্ধ" in ACCESS_DENIED_MESSAGE_BN
    assert "আবু হুরাইরার" in ACCESS_DENIED_MESSAGE_BN
    print("  ✅ Access Denied message verified.")

    print("\n========================================")
    print("🎉 ALL SECURITY & ADMIN LOCK TESTS PASSED! (100% SECURE)")
    print("========================================")

if __name__ == "__main__":
    test_admin_lock()