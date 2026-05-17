"""
REST API tests for employee metadata / lifecycle controllers:

  EmployeesAuditLogController     — /api/v1/employees-audit-log
  EmployeesStatusHistoryController— /api/v1/employees-status-history
  EmployeesPreferencesController  — /api/v1/employees-preferences
  EmployeesSettingsController     — /api/v1/employees-settings
  EmployeesSsnController          — /api/v1/employees-ssn

Standard CRUD pattern:
  POST   /      → 201
  GET    /      → 200 list
  GET    /count → 200 integer
  GET    /{id}  → 200 or 404
  HEAD   /{id}  → 200 or 404
  PUT    /{id}  → 200 or 404
  DELETE /{id}  → 204 or 404
"""

import time as _time
import allure
import pytest
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_resource(emp_url, path, payload, authed_session, auth_headers):
    resp = authed_session.post(f"{emp_url}/{path}", json=payload, headers=auth_headers)
    if resp.status_code != 201:
        pytest.skip(f"Could not create {path}: {resp.status_code} {resp.text[:200]}")
    return resp.json()


def _get_any_employee_id(emp_url, authed_session, auth_headers):
    resp = authed_session.get(f"{emp_url}/employees", headers=auth_headers)
    resp.raise_for_status()
    employees = resp.json()
    if not employees:
        pytest.skip("No employees available for metadata tests")
    return employees[0]["employeeId"]


def _now_iso():
    return _time.strftime("%Y-%m-%dT%H:%M:%S", _time.gmtime())


# ===========================================================================
# EmployeesAuditLogController — /api/v1/employees-audit-log
# Fields: employeeId, action, actionTimestamp, actionBy  →  employeeAuditLogId
# ===========================================================================

def _audit_payload(employee_id):
    return {
        "employeeId": employee_id,
        "action": "TEST_ACTION",
        "actionTimestamp": _now_iso(),
        "actionBy": employee_id,
    }


@allure.suite("User Service – Metadata")
@allure.feature("Employees Audit Log")
@pytest.mark.employee_metadata
class TestEmployeesAuditLog:

    @allure.title("POST /employees-audit-log — creates log entry, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_audit_log(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees-audit-log")
        allure.dynamic.tag("smoke", "audit-log")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)

        with allure.step("POST /employees-audit-log"):
            resp = authed_session.post(f"{emp_url}/employees-audit-log", json=_audit_payload(employee_id), headers=auth_headers)

        with allure.step("Assert 201 and employeeAuditLogId"):
            assert resp.status_code == 201
            assert "employeeAuditLogId" in resp.json()

    @allure.title("GET /employees-audit-log — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_audit_logs(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-audit-log")
        allure.dynamic.tag("smoke", "audit-log")

        resp = authed_session.get(f"{emp_url}/employees-audit-log", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /employees-audit-log/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_audit_logs(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-audit-log/count")
        allure.dynamic.tag("smoke", "audit-log")

        resp = authed_session.get(f"{emp_url}/employees-audit-log/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /employees-audit-log/{id} — returns log for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_audit_log_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-audit-log/{id}")
        allure.dynamic.tag("smoke", "audit-log")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-audit-log", _audit_payload(employee_id), authed_session, auth_headers)
        log_id = created["employeeAuditLogId"]

        with allure.step(f"GET /employees-audit-log/{log_id}"):
            resp = authed_session.get(f"{emp_url}/employees-audit-log/{log_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching id"):
            assert resp.status_code == 200
            assert resp.json()["employeeAuditLogId"] == log_id

    @allure.title("GET /employees-audit-log/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_audit_log_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-audit-log/{id}")
        allure.dynamic.tag("negative", "audit-log")

        resp = authed_session.get(f"{emp_url}/employees-audit-log/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("HEAD /employees-audit-log/{id} — 200 for existing, 404 for missing")
    @allure.severity(allure.severity_level.NORMAL)
    def test_head_audit_log(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /employees-audit-log/{id}")
        allure.dynamic.tag("smoke", "audit-log")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-audit-log", _audit_payload(employee_id), authed_session, auth_headers)
        log_id = created["employeeAuditLogId"]

        assert authed_session.head(f"{emp_url}/employees-audit-log/{log_id}", headers=auth_headers).status_code == 200
        assert authed_session.head(f"{emp_url}/employees-audit-log/9999999", headers=auth_headers).status_code == 404

    @allure.title("PUT /employees-audit-log/{id} — updates action field")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_audit_log(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /employees-audit-log/{id}")
        allure.dynamic.tag("smoke", "audit-log")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-audit-log", _audit_payload(employee_id), authed_session, auth_headers)
        log_id = created["employeeAuditLogId"]

        with allure.step(f"PUT /employees-audit-log/{log_id}"):
            payload = {**created, "action": "UPDATED_ACTION"}
            resp = authed_session.put(f"{emp_url}/employees-audit-log/{log_id}", json=payload, headers=auth_headers)

        with allure.step("Assert 200 and updated action"):
            assert resp.status_code == 200
            assert resp.json()["action"] == "UPDATED_ACTION"

    @allure.title("DELETE /employees-audit-log/{id} — deletes log entry, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_audit_log(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-audit-log/{id}")
        allure.dynamic.tag("smoke", "audit-log")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-audit-log", _audit_payload(employee_id), authed_session, auth_headers)
        log_id = created["employeeAuditLogId"]

        with allure.step(f"DELETE /employees-audit-log/{log_id}"):
            resp = authed_session.delete(f"{emp_url}/employees-audit-log/{log_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("POST /employees-audit-log without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_audit_log_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees-audit-log")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/employees-audit-log", json={"employeeId": 1, "action": "X", "actionTimestamp": _now_iso(), "actionBy": 1})
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# EmployeesStatusHistoryController — /api/v1/employees-status-history
# Fields: employeeId, status, changedAt, changedByEmployeeId
#   →  employeeStatusHistoryId
# ===========================================================================

def _status_history_payload(employee_id):
    return {
        "employeeId": employee_id,
        "status": 1,
        "changedAt": _now_iso(),
        "changedByEmployeeId": employee_id,
    }


@allure.suite("User Service – Metadata")
@allure.feature("Employees Status History")
@pytest.mark.employee_metadata
class TestEmployeesStatusHistory:

    @allure.title("POST /employees-status-history — creates history record, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_status_history(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees-status-history")
        allure.dynamic.tag("smoke", "status-history")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)

        with allure.step("POST /employees-status-history"):
            resp = authed_session.post(f"{emp_url}/employees-status-history", json=_status_history_payload(employee_id), headers=auth_headers)

        with allure.step("Assert 201 and employeeStatusHistoryId"):
            assert resp.status_code == 201
            assert "employeeStatusHistoryId" in resp.json()

    @allure.title("GET /employees-status-history — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_status_history(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-status-history")
        allure.dynamic.tag("smoke", "status-history")

        resp = authed_session.get(f"{emp_url}/employees-status-history", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /employees-status-history/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_status_history(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-status-history/count")
        allure.dynamic.tag("smoke", "status-history")

        resp = authed_session.get(f"{emp_url}/employees-status-history/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /employees-status-history/{id} — returns record for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_status_history_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-status-history/{id}")
        allure.dynamic.tag("smoke", "status-history")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-status-history", _status_history_payload(employee_id), authed_session, auth_headers)
        hist_id = created["employeeStatusHistoryId"]

        with allure.step(f"GET /employees-status-history/{hist_id}"):
            resp = authed_session.get(f"{emp_url}/employees-status-history/{hist_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching id"):
            assert resp.status_code == 200
            assert resp.json()["employeeStatusHistoryId"] == hist_id

    @allure.title("GET /employees-status-history/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_status_history_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-status-history/{id}")
        allure.dynamic.tag("negative", "status-history")

        resp = authed_session.get(f"{emp_url}/employees-status-history/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("PUT /employees-status-history/{id} — updates status")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_status_history(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /employees-status-history/{id}")
        allure.dynamic.tag("smoke", "status-history")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-status-history", _status_history_payload(employee_id), authed_session, auth_headers)
        hist_id = created["employeeStatusHistoryId"]

        with allure.step(f"PUT /employees-status-history/{hist_id}"):
            payload = {**created, "status": 0}
            resp = authed_session.put(f"{emp_url}/employees-status-history/{hist_id}", json=payload, headers=auth_headers)

        with allure.step("Assert 200 and updated status"):
            assert resp.status_code == 200
            assert resp.json()["status"] == 0

    @allure.title("DELETE /employees-status-history/{id} — deletes record, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_status_history(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-status-history/{id}")
        allure.dynamic.tag("smoke", "status-history")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-status-history", _status_history_payload(employee_id), authed_session, auth_headers)
        hist_id = created["employeeStatusHistoryId"]

        with allure.step(f"DELETE /employees-status-history/{hist_id}"):
            resp = authed_session.delete(f"{emp_url}/employees-status-history/{hist_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("POST /employees-status-history without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_status_history_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees-status-history")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/employees-status-history", json={"employeeId": 1, "status": 1, "changedAt": _now_iso(), "changedByEmployeeId": 1})
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# EmployeesPreferencesController — /api/v1/employees-preferences
# Fields: employeeId, preferenceKey, preferenceDescription
#   →  employeePreferenceId
# ===========================================================================

def _preference_payload(employee_id, tag="pref"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    return {
        "employeeId": employee_id,
        "preferenceKey": uid,
        "preferenceDescription": "Test preference",
    }


@allure.suite("User Service – Metadata")
@allure.feature("Employees Preferences")
@pytest.mark.employee_metadata
class TestEmployeesPreferences:

    @allure.title("POST /employees-preferences — creates preference, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_preference(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees-preferences")
        allure.dynamic.tag("smoke", "preferences")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)

        with allure.step("POST /employees-preferences"):
            resp = authed_session.post(f"{emp_url}/employees-preferences", json=_preference_payload(employee_id, "smoke"), headers=auth_headers)

        with allure.step("Assert 201 and employeePreferenceId"):
            assert resp.status_code == 201
            assert "employeePreferenceId" in resp.json()

    @allure.title("GET /employees-preferences — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_preferences(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-preferences")
        allure.dynamic.tag("smoke", "preferences")

        resp = authed_session.get(f"{emp_url}/employees-preferences", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /employees-preferences/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_preferences(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-preferences/count")
        allure.dynamic.tag("smoke", "preferences")

        resp = authed_session.get(f"{emp_url}/employees-preferences/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /employees-preferences/{id} — returns preference for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_preference_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-preferences/{id}")
        allure.dynamic.tag("smoke", "preferences")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-preferences", _preference_payload(employee_id, "getid"), authed_session, auth_headers)
        pref_id = created["employeePreferenceId"]

        with allure.step(f"GET /employees-preferences/{pref_id}"):
            resp = authed_session.get(f"{emp_url}/employees-preferences/{pref_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching id"):
            assert resp.status_code == 200
            assert resp.json()["employeePreferenceId"] == pref_id

    @allure.title("GET /employees-preferences/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_preference_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-preferences/{id}")
        allure.dynamic.tag("negative", "preferences")

        resp = authed_session.get(f"{emp_url}/employees-preferences/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("HEAD /employees-preferences/{id} — 200 for existing, 404 for missing")
    @allure.severity(allure.severity_level.NORMAL)
    def test_head_preference(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /employees-preferences/{id}")
        allure.dynamic.tag("smoke", "preferences")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-preferences", _preference_payload(employee_id, "head"), authed_session, auth_headers)
        pref_id = created["employeePreferenceId"]

        assert authed_session.head(f"{emp_url}/employees-preferences/{pref_id}", headers=auth_headers).status_code == 200
        assert authed_session.head(f"{emp_url}/employees-preferences/9999999", headers=auth_headers).status_code == 404

    @allure.title("PUT /employees-preferences/{id} — updates preferenceDescription")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_preference(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /employees-preferences/{id}")
        allure.dynamic.tag("smoke", "preferences")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-preferences", _preference_payload(employee_id, "upd"), authed_session, auth_headers)
        pref_id = created["employeePreferenceId"]

        with allure.step(f"PUT /employees-preferences/{pref_id}"):
            payload = {**created, "preferenceDescription": "Updated description"}
            resp = authed_session.put(f"{emp_url}/employees-preferences/{pref_id}", json=payload, headers=auth_headers)

        with allure.step("Assert 200 and updated description"):
            assert resp.status_code == 200
            assert resp.json()["preferenceDescription"] == "Updated description"

    @allure.title("DELETE /employees-preferences/{id} — deletes preference, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_preference(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-preferences/{id}")
        allure.dynamic.tag("smoke", "preferences")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-preferences", _preference_payload(employee_id, "del"), authed_session, auth_headers)
        pref_id = created["employeePreferenceId"]

        with allure.step(f"DELETE /employees-preferences/{pref_id}"):
            resp = authed_session.delete(f"{emp_url}/employees-preferences/{pref_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("POST /employees-preferences without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_preference_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees-preferences")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/employees-preferences", json={"employeeId": 1, "preferenceKey": "k", "preferenceDescription": "d"})
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# EmployeesSettingsController — /api/v1/employees-settings
# Fields: employeeId, settingKey, settingDescription  →  employeeSettingId
# ===========================================================================

def _setting_payload(employee_id, tag="set"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    return {
        "employeeId": employee_id,
        "settingKey": uid,
        "settingDescription": "Test setting",
    }


@allure.suite("User Service – Metadata")
@allure.feature("Employees Settings")
@pytest.mark.employee_metadata
class TestEmployeesSettings:

    @allure.title("POST /employees-settings — creates setting, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_setting(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees-settings")
        allure.dynamic.tag("smoke", "settings")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)

        with allure.step("POST /employees-settings"):
            resp = authed_session.post(f"{emp_url}/employees-settings", json=_setting_payload(employee_id, "smoke"), headers=auth_headers)

        with allure.step("Assert 201 and employeeSettingId"):
            assert resp.status_code == 201
            assert "employeeSettingId" in resp.json()

    @allure.title("GET /employees-settings — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_settings(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-settings")
        allure.dynamic.tag("smoke", "settings")

        resp = authed_session.get(f"{emp_url}/employees-settings", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /employees-settings/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_settings(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-settings/count")
        allure.dynamic.tag("smoke", "settings")

        resp = authed_session.get(f"{emp_url}/employees-settings/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /employees-settings/{id} — returns setting for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_setting_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-settings/{id}")
        allure.dynamic.tag("smoke", "settings")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-settings", _setting_payload(employee_id, "getid"), authed_session, auth_headers)
        setting_id = created["employeeSettingId"]

        with allure.step(f"GET /employees-settings/{setting_id}"):
            resp = authed_session.get(f"{emp_url}/employees-settings/{setting_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching id"):
            assert resp.status_code == 200
            assert resp.json()["employeeSettingId"] == setting_id

    @allure.title("GET /employees-settings/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_setting_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-settings/{id}")
        allure.dynamic.tag("negative", "settings")

        resp = authed_session.get(f"{emp_url}/employees-settings/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("PUT /employees-settings/{id} — updates settingDescription")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_setting(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /employees-settings/{id}")
        allure.dynamic.tag("smoke", "settings")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-settings", _setting_payload(employee_id, "upd"), authed_session, auth_headers)
        setting_id = created["employeeSettingId"]

        with allure.step(f"PUT /employees-settings/{setting_id}"):
            payload = {**created, "settingDescription": "Updated description"}
            resp = authed_session.put(f"{emp_url}/employees-settings/{setting_id}", json=payload, headers=auth_headers)

        with allure.step("Assert 200 and updated description"):
            assert resp.status_code == 200
            assert resp.json()["settingDescription"] == "Updated description"

    @allure.title("DELETE /employees-settings/{id} — deletes setting, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_setting(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-settings/{id}")
        allure.dynamic.tag("smoke", "settings")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-settings", _setting_payload(employee_id, "del"), authed_session, auth_headers)
        setting_id = created["employeeSettingId"]

        with allure.step(f"DELETE /employees-settings/{setting_id}"):
            resp = authed_session.delete(f"{emp_url}/employees-settings/{setting_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("POST /employees-settings without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_setting_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees-settings")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/employees-settings", json={"employeeId": 1, "settingKey": "k", "settingDescription": "d"})
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# EmployeesSsnController — /api/v1/employees-ssn
# Fields: employeeId, ssn  →  employeeSsnId
#
# NOTE: SSN is sensitive PII. Tests use synthetic (non-real) values only.
#       The format "000-00-XXXX" is never issued by the SSA.
# ===========================================================================

def _ssn_payload(employee_id, tag="ssn"):
    uid = int(_time.time() * 1000) % 9000 + 1000
    return {
        "employeeId": employee_id,
        "ssn": f"000-00-{uid}",
    }


@allure.suite("User Service – Metadata")
@allure.feature("Employees SSN")
@pytest.mark.employee_metadata
class TestEmployeesSsn:

    @allure.title("POST /employees-ssn — creates SSN record, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_ssn(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees-ssn")
        allure.dynamic.tag("smoke", "ssn")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)

        with allure.step("POST /employees-ssn with synthetic SSN"):
            resp = authed_session.post(f"{emp_url}/employees-ssn", json=_ssn_payload(employee_id), headers=auth_headers)

        with allure.step("Assert 201 and employeeSsnId"):
            assert resp.status_code == 201
            assert "employeeSsnId" in resp.json()

    @allure.title("GET /employees-ssn — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_ssn(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-ssn")
        allure.dynamic.tag("smoke", "ssn")

        resp = authed_session.get(f"{emp_url}/employees-ssn", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /employees-ssn/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_ssn(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-ssn/count")
        allure.dynamic.tag("smoke", "ssn")

        resp = authed_session.get(f"{emp_url}/employees-ssn/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /employees-ssn/{id} — returns record for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_ssn_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-ssn/{id}")
        allure.dynamic.tag("smoke", "ssn")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-ssn", _ssn_payload(employee_id), authed_session, auth_headers)
        ssn_id = created["employeeSsnId"]

        with allure.step(f"GET /employees-ssn/{ssn_id}"):
            resp = authed_session.get(f"{emp_url}/employees-ssn/{ssn_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching id"):
            assert resp.status_code == 200
            assert resp.json()["employeeSsnId"] == ssn_id

    @allure.title("GET /employees-ssn/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_ssn_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-ssn/{id}")
        allure.dynamic.tag("negative", "ssn")

        resp = authed_session.get(f"{emp_url}/employees-ssn/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("HEAD /employees-ssn/{id} — 200 for existing, 404 for missing")
    @allure.severity(allure.severity_level.NORMAL)
    def test_head_ssn(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /employees-ssn/{id}")
        allure.dynamic.tag("smoke", "ssn")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-ssn", _ssn_payload(employee_id), authed_session, auth_headers)
        ssn_id = created["employeeSsnId"]

        assert authed_session.head(f"{emp_url}/employees-ssn/{ssn_id}", headers=auth_headers).status_code == 200
        assert authed_session.head(f"{emp_url}/employees-ssn/9999999", headers=auth_headers).status_code == 404

    @allure.title("PUT /employees-ssn/{id} — updates SSN value")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_ssn(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /employees-ssn/{id}")
        allure.dynamic.tag("smoke", "ssn")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-ssn", _ssn_payload(employee_id), authed_session, auth_headers)
        ssn_id = created["employeeSsnId"]

        with allure.step(f"PUT /employees-ssn/{ssn_id}"):
            payload = {**created, "ssn": "000-00-9999"}
            resp = authed_session.put(f"{emp_url}/employees-ssn/{ssn_id}", json=payload, headers=auth_headers)

        with allure.step("Assert 200 and updated SSN"):
            assert resp.status_code == 200
            assert resp.json()["ssn"] == "000-00-9999"

    @allure.title("DELETE /employees-ssn/{id} — deletes record, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_ssn(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-ssn/{id}")
        allure.dynamic.tag("smoke", "ssn")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "employees-ssn", _ssn_payload(employee_id), authed_session, auth_headers)
        ssn_id = created["employeeSsnId"]

        with allure.step(f"DELETE /employees-ssn/{ssn_id}"):
            resp = authed_session.delete(f"{emp_url}/employees-ssn/{ssn_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("DELETE /employees-ssn/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_ssn_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-ssn/{id}")
        allure.dynamic.tag("negative", "ssn")

        resp = authed_session.delete(f"{emp_url}/employees-ssn/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("POST /employees-ssn without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_ssn_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees-ssn")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/employees-ssn", json={"employeeId": 1, "ssn": "000-00-0001"})
        assert resp.status_code in (401, 403, 404)
