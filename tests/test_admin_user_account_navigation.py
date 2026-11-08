from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "backend/app/static/admin/console.html").read_text(encoding="utf-8")
JS = (ROOT / "backend/app/static/admin/console.js").read_text(encoding="utf-8")
CSS = (ROOT / "backend/app/static/admin/console.css").read_text(encoding="utf-8")


def test_user_and_account_management_is_a_single_sidebar_group():
    assert 'id="userManagementToggle"' in HTML
    assert 'aria-controls="userManagementSubnav"' in HTML
    assert 'id="userManagementSubnav"' in HTML
    assert 'data-page="users"' not in HTML
    assert 'data-permission="users:read"' in HTML


def test_user_account_group_exposes_existing_management_workflows():
    for action in ("directory", "create", "lifecycle", "bulk", "export"):
        assert f'data-user-action="{action}"' in HTML

    assert 'id="userDirectoryPanel"' in HTML
    assert 'id="userCreateForm"' in HTML
    assert 'id="bulkUsersPanel"' in HTML
    assert 'id="exportUsersCsv"' in HTML


def test_user_account_navigation_respects_permissions_and_localization():
    assert '.nav-subitem[data-permission]' in JS
    assert 'users:create' in HTML
    assert 'users:update' in HTML
    assert 'userNavDirectory:' in JS
    assert 'userNavLifecycle:' in JS
    assert 'userNavBulk:' in JS
    assert 'userNavExport:' in JS


def test_user_account_submenu_has_responsive_active_states():
    assert '.nav-subitem.active' in CSS
    assert '.nav-group-toggle[aria-expanded="true"]' in CSS
    assert '@media(max-width:760px)' in CSS
