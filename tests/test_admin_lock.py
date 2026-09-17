"""
Security & Admin Lock Verification Test.
Ensures ONLY the Primary Admin (Abu Huraira: 8953572486) can access the bot,
and any other user ID is strictly rejected.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    PRIMARY_ADMIN_ID,
    ADMIN_IDS,
    ONLY_ADMIN_ACCESS,
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

    assert ONLY_ADMIN_ACCESS is True, "Admin access lock must be enabled"
    assert PRIMARY_ADMIN_ID == 8953572486, "Primary Admin ID mismatch"
    assert 8953572486 in ADMIN_IDS, "Primary Admin must be in ADMIN_IDS"

    # 1. Test Admin User (Abu Huraira)
    print("\n[1/3] Testing Authorized Developer / Admin (8953572486)...")
    auth_result = is_authorized(8953572486)
    print(f"  Result for Abu Huraira (8953572486): Authorized = {auth_result}")
    assert auth_result is True, "Admin MUST be authorized!"
    print("  ✅ Admin access GRANTED.")

    # 2. Test Unauthorized Stranger Users
    print("\n[2/3] Testing Unauthorized Strangers & Random Users...")
    strangers = [123456, 987654321, 11223344, 999999999, 0, None]
    for uid in strangers:
        res = is_authorized(uid)
        print(f"  Testing User ID {uid}: Authorized = {res}")
        assert res is False, f"User {uid} must NOT be authorized!"
    print("  ✅ All unauthorized users successfully BLOCKED.")

    # 3. Test Rejection Message
    print("\n[3/3] Testing Access Denied Message...")
    assert "অ্যাক্সেস সীমাবদ্ধ" in ACCESS_DENIED_MESSAGE_BN
    assert "আবু হুরাইরার" in ACCESS_DENIED_MESSAGE_BN
    print("  ✅ Access Denied message verified:")
    print("  --------------------------------------")
    print(ACCESS_DENIED_MESSAGE_BN)
    print("  --------------------------------------")

    print("\n========================================")
    print("🎉 ALL SECURITY & ADMIN LOCK TESTS PASSED! (100% SECURE)")
    print("========================================")

if __name__ == "__main__":
    test_admin_lock()