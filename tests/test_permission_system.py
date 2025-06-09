"""
權限系統測試
"""
import pytest
from src.auth.models import UserRole
from src.auth.services.permission_service import (
    Permission,
    RolePermissions
)

def test_client_permissions():
    """測試一般使用者權限"""
    permissions = RolePermissions.get_permissions_by_role(UserRole.CLIENT)
    
    # 一般使用者應該有的權限
    assert Permission.VIEW_COURSES in permissions
    assert Permission.VIEW_PRACTICE_RECORDS in permissions
    assert Permission.CREATE_PRACTICE_RECORDS in permissions
    assert Permission.CHAT_WITH_THERAPIST in permissions
    
    # 一般使用者不應該有的權限
    assert Permission.EDIT_COURSES not in permissions
    assert Permission.DELETE_COURSES not in permissions
    assert Permission.CREATE_COURSES not in permissions
    assert Permission.MANAGE_USERS not in permissions
    assert Permission.CHAT_WITH_CLIENT not in permissions

def test_therapist_permissions():
    """測試語言治療師權限"""
    permissions = RolePermissions.get_permissions_by_role(UserRole.THERAPIST)
    
    # 語言治療師應該有的權限
    assert Permission.VIEW_COURSES in permissions
    assert Permission.VIEW_PRACTICE_RECORDS in permissions
    assert Permission.CHAT_WITH_CLIENT in permissions
    
    # 語言治療師不應該有的權限
    assert Permission.EDIT_COURSES not in permissions
    assert Permission.DELETE_COURSES not in permissions
    assert Permission.CREATE_COURSES not in permissions
    assert Permission.MANAGE_USERS not in permissions
    assert Permission.CREATE_PRACTICE_RECORDS not in permissions
    assert Permission.CHAT_WITH_THERAPIST not in permissions

def test_admin_permissions():
    """測試管理員權限"""
    permissions = RolePermissions.get_permissions_by_role(UserRole.ADMIN)
    
    # 管理員應該有所有權限
    assert Permission.VIEW_COURSES in permissions
    assert Permission.EDIT_COURSES in permissions
    assert Permission.DELETE_COURSES in permissions
    assert Permission.CREATE_COURSES in permissions
    assert Permission.VIEW_PRACTICE_RECORDS in permissions
    assert Permission.CHAT_WITH_THERAPIST in permissions
    assert Permission.CHAT_WITH_CLIENT in permissions
    assert Permission.MANAGE_USERS in permissions
    assert Permission.VIEW_ALL_USERS in permissions

def test_role_permission_hierarchy():
    """測試角色權限層級"""
    client_perms = set(RolePermissions.get_permissions_by_role(UserRole.CLIENT))
    therapist_perms = set(RolePermissions.get_permissions_by_role(UserRole.THERAPIST))
    admin_perms = set(RolePermissions.get_permissions_by_role(UserRole.ADMIN))
    
    # 管理員應該有最多權限
    assert len(admin_perms) >= len(therapist_perms)
    assert len(admin_perms) >= len(client_perms)
    
    # 確保權限不重疊但互補
    # 一般使用者和語言治療師有不同的溝通權限
    assert Permission.CHAT_WITH_THERAPIST in client_perms
    assert Permission.CHAT_WITH_CLIENT in therapist_perms
    assert Permission.CHAT_WITH_THERAPIST not in therapist_perms
    assert Permission.CHAT_WITH_CLIENT not in client_perms

def test_permission_constants():
    """測試權限常數定義"""
    # 確保所有權限都有定義
    expected_permissions = [
        "view_courses",
        "edit_courses", 
        "delete_courses",
        "create_courses",
        "view_practice_records",
        "create_practice_records",
        "chat_with_therapist",
        "chat_with_client",
        "manage_users",
        "view_all_users"
    ]
    
    for perm in expected_permissions:
        assert hasattr(Permission, perm.upper())

def test_unknown_role():
    """測試未知角色"""
    # 模擬一個不存在的角色
    permissions = RolePermissions.get_permissions_by_role("unknown_role")
    assert permissions == []

if __name__ == "__main__":
    # 執行所有測試
    test_client_permissions()
    test_therapist_permissions() 
    test_admin_permissions()
    test_role_permission_hierarchy()
    test_permission_constants()
    test_unknown_role()
    
    print("✅ 所有權限系統測試通過！")
