"""
REST API tests for employee reference-data controllers:

  DepartmentsController      — /api/v1/departments
  EmployeesRolesController   — /api/v1/employees-roles
  PermissioinsController     — /api/v1/permissions   (class typo: "Permissioins")
  RolePermissionsController  — /api/v1/role-permissions
  OrganizationController     — /api/v1/organization
  ProjectsController         — /api/v1/projects

All controllers follow the same standard CRUD pattern:
  POST   /          → 201 CREATED
  GET    /          → 200 list
  GET    /count     → 200 integer
  GET    /{id}      → 200 or 404
  HEAD   /{id}      → 200 or 404
  PUT    /{id}      → 200 or 404
  DELETE /{id}      → 204 or 404
"""

import time as _time
import allure
import pytest
import requests


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _create_resource(emp_url, path, payload, authed_session, auth_headers):
    resp = authed_session.post(f"{emp_url}/{path}", json=payload, headers=auth_headers)
    if resp.status_code != 201:
        pytest.skip(f"Could not create {path}: {resp.status_code} {resp.text[:200]}")
    return resp.json()


def _id_key(body):
    """Return the primary-key value from any response body dict."""
    for key in body:
        if key.endswith("Id") or key.endswith("ID"):
            return body[key]
    return None


def _assert_crud(emp_url, path, create_payload, update_payload, id_field,
                 authed_session, auth_headers):
    """Smoke-test the full CRUD cycle for a standard endpoint."""
    created = _create_resource(emp_url, path, create_payload, authed_session, auth_headers)
    resource_id = created[id_field]

    # GET by id
    resp = authed_session.get(f"{emp_url}/{path}/{resource_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()[id_field] == resource_id

    # HEAD
    resp = authed_session.head(f"{emp_url}/{path}/{resource_id}", headers=auth_headers)
    assert resp.status_code == 200

    # PUT
    resp = authed_session.put(f"{emp_url}/{path}/{resource_id}", json=update_payload, headers=auth_headers)
    assert resp.status_code == 200

    # DELETE
    resp = authed_session.delete(f"{emp_url}/{path}/{resource_id}", headers=auth_headers)
    assert resp.status_code == 204


# ===========================================================================
# DepartmentsController — /api/v1/departments
# Fields: department, description, status  →  departmentId
# ===========================================================================

def _dept_payload(tag="dept"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    return {"department": uid, "description": "Test department", "status": 1}


@allure.suite("User Service – Reference Data")
@allure.feature("Departments")
@pytest.mark.employee_ref_data
class TestDepartments:

    @allure.title("POST /departments — creates department, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_department(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /departments")
        allure.dynamic.tag("smoke", "departments")

        with allure.step("POST /departments with valid payload"):
            resp = authed_session.post(f"{emp_url}/departments", json=_dept_payload("smoke"), headers=auth_headers)

        with allure.step("Assert 201 and departmentId present"):
            assert resp.status_code == 201
            assert "departmentId" in resp.json()

    @allure.title("GET /departments — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_departments(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /departments")
        allure.dynamic.tag("smoke", "departments")

        with allure.step("GET /departments"):
            resp = authed_session.get(f"{emp_url}/departments", headers=auth_headers)

        with allure.step("Assert 200 and list"):
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)

    @allure.title("GET /departments/count — returns integer count")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_departments(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /departments/count")
        allure.dynamic.tag("smoke", "departments")

        with allure.step("GET /departments/count"):
            resp = authed_session.get(f"{emp_url}/departments/count", headers=auth_headers)

        with allure.step("Assert 200 and integer"):
            assert resp.status_code == 200
            assert isinstance(resp.json(), int)

    @allure.title("GET /departments/{id} — returns department for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_department_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /departments/{id}")
        allure.dynamic.tag("smoke", "departments")

        created = _create_resource(emp_url, "departments", _dept_payload("getid"), authed_session, auth_headers)
        dept_id = created["departmentId"]

        with allure.step(f"GET /departments/{dept_id}"):
            resp = authed_session.get(f"{emp_url}/departments/{dept_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching departmentId"):
            assert resp.status_code == 200
            assert resp.json()["departmentId"] == dept_id

    @allure.title("GET /departments/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_department_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /departments/{id}")
        allure.dynamic.tag("negative", "departments")

        with allure.step("GET /departments/9999999"):
            resp = authed_session.get(f"{emp_url}/departments/9999999", headers=auth_headers)

        with allure.step("Assert 404"):
            assert resp.status_code == 404

    @allure.title("HEAD /departments/{id} — 200 for existing, 404 for missing")
    @allure.severity(allure.severity_level.NORMAL)
    def test_head_department(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /departments/{id}")
        allure.dynamic.tag("smoke", "departments")

        created = _create_resource(emp_url, "departments", _dept_payload("head"), authed_session, auth_headers)
        dept_id = created["departmentId"]

        with allure.step(f"HEAD /departments/{dept_id}"):
            resp = authed_session.head(f"{emp_url}/departments/{dept_id}", headers=auth_headers)
        assert resp.status_code == 200

        with allure.step("HEAD /departments/9999999"):
            resp = authed_session.head(f"{emp_url}/departments/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("PUT /departments/{id} — updates department name")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_department(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /departments/{id}")
        allure.dynamic.tag("smoke", "departments")

        created = _create_resource(emp_url, "departments", _dept_payload("upd"), authed_session, auth_headers)
        dept_id = created["departmentId"]

        with allure.step(f"PUT /departments/{dept_id}"):
            payload = {**created, "description": "Updated description"}
            resp = authed_session.put(f"{emp_url}/departments/{dept_id}", json=payload, headers=auth_headers)

        with allure.step("Assert 200 and updated description"):
            assert resp.status_code == 200
            assert resp.json()["description"] == "Updated description"

    @allure.title("DELETE /departments/{id} — deletes department, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_department(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /departments/{id}")
        allure.dynamic.tag("smoke", "departments")

        created = _create_resource(emp_url, "departments", _dept_payload("del"), authed_session, auth_headers)
        dept_id = created["departmentId"]

        with allure.step(f"DELETE /departments/{dept_id}"):
            resp = authed_session.delete(f"{emp_url}/departments/{dept_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("POST/GET/PUT/DELETE /departments without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("method,path", [
        ("get", "/departments"),
        ("post", "/departments"),
        ("put", "/departments/1"),
        ("delete", "/departments/1"),
    ])
    def test_departments_no_auth(self, emp_url, method, path):
        allure.dynamic.label("endpoint", f"{method.upper()} {path}")
        allure.dynamic.tag("negative", "auth")

        with allure.step(f"{method.upper()} {path} without auth"):
            resp = getattr(requests, method)(f"{emp_url}{path}", json={})

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ===========================================================================
# EmployeesRolesController — /api/v1/employees-roles
# Fields: role, description  →  employeeRoleId
# ===========================================================================

def _role_payload(tag="role"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    return {"role": uid, "description": "Test role"}


@allure.suite("User Service – Reference Data")
@allure.feature("Employee Roles")
@pytest.mark.employee_ref_data
class TestEmployeesRoles:

    @allure.title("POST /employees-roles — creates role, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_role(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees-roles")
        allure.dynamic.tag("smoke", "roles")

        with allure.step("POST /employees-roles"):
            resp = authed_session.post(f"{emp_url}/employees-roles", json=_role_payload("smoke"), headers=auth_headers)

        with allure.step("Assert 201 and employeeRoleId"):
            assert resp.status_code == 201
            assert "employeeRoleId" in resp.json()

    @allure.title("GET /employees-roles — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_roles(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-roles")
        allure.dynamic.tag("smoke", "roles")

        resp = authed_session.get(f"{emp_url}/employees-roles", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /employees-roles/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_roles(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-roles/count")
        allure.dynamic.tag("smoke", "roles")

        resp = authed_session.get(f"{emp_url}/employees-roles/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("Full CRUD cycle — /employees-roles")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_role_crud_cycle(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "CRUD /employees-roles")
        allure.dynamic.tag("smoke", "roles")

        _assert_crud(
            emp_url, "employees-roles",
            create_payload=_role_payload("crud"),
            update_payload={"role": "UpdatedRole", "description": "Updated"},
            id_field="employeeRoleId",
            authed_session=authed_session,
            auth_headers=auth_headers,
        )

    @allure.title("GET /employees-roles/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_role_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-roles/{id}")
        allure.dynamic.tag("negative", "roles")

        resp = authed_session.get(f"{emp_url}/employees-roles/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("POST /employees-roles without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_role_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees-roles")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/employees-roles", json=_role_payload("noauth"))
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# PermissioinsController — /api/v1/permissions  (class typo: "Permissioins")
# Fields: permissionTag, permissionName, description  →  permissioinsId
# ===========================================================================

def _perm_payload(tag="perm"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    return {"permissionTag": uid, "permissionName": f"Permission {uid}", "description": "Test permission"}


@allure.suite("User Service – Reference Data")
@allure.feature("Permissions")
@pytest.mark.employee_ref_data
class TestPermissions:

    @allure.title("POST /permissions — creates permission, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_permission(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /permissions")
        allure.dynamic.tag("smoke", "permissions")

        with allure.step("POST /permissions"):
            resp = authed_session.post(f"{emp_url}/permissions", json=_perm_payload("smoke"), headers=auth_headers)

        with allure.step("Assert 201 and permissioinsId"):
            assert resp.status_code == 201
            assert "permissioinsId" in resp.json()

    @allure.title("GET /permissions — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_permissions(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /permissions")
        allure.dynamic.tag("smoke", "permissions")

        resp = authed_session.get(f"{emp_url}/permissions", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /permissions/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_permissions(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /permissions/count")
        allure.dynamic.tag("smoke", "permissions")

        resp = authed_session.get(f"{emp_url}/permissions/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("Full CRUD cycle — /permissions")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_permission_crud_cycle(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "CRUD /permissions")
        allure.dynamic.tag("smoke", "permissions")

        _assert_crud(
            emp_url, "permissions",
            create_payload=_perm_payload("crud"),
            update_payload={"permissionTag": "UPDATED", "permissionName": "Updated Perm", "description": "Updated"},
            id_field="permissioinsId",
            authed_session=authed_session,
            auth_headers=auth_headers,
        )

    @allure.title("GET /permissions/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_permission_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /permissions/{id}")
        allure.dynamic.tag("negative", "permissions")

        resp = authed_session.get(f"{emp_url}/permissions/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("POST /permissions without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_permission_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /permissions")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/permissions", json=_perm_payload("noauth"))
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# RolePermissionsController — /api/v1/role-permissions
# Fields: employeeRoleId, permissioinsId  →  rolePermissionId
# ===========================================================================

def _create_role_and_perm(emp_url, authed_session, auth_headers):
    role = _create_resource(emp_url, "employees-roles", _role_payload("rp"), authed_session, auth_headers)
    perm = _create_resource(emp_url, "permissions", _perm_payload("rp"), authed_session, auth_headers)
    return role["employeeRoleId"], perm["permissioinsId"]


@allure.suite("User Service – Reference Data")
@allure.feature("Role Permissions")
@pytest.mark.employee_ref_data
class TestRolePermissions:

    @allure.title("POST /role-permissions — creates link, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_role_permission(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /role-permissions")
        allure.dynamic.tag("smoke", "role-permissions")

        role_id, perm_id = _create_role_and_perm(emp_url, authed_session, auth_headers)
        payload = {"employeeRoleId": role_id, "permissioinsId": perm_id}

        with allure.step("POST /role-permissions"):
            resp = authed_session.post(f"{emp_url}/role-permissions", json=payload, headers=auth_headers)

        with allure.step("Assert 201 and rolePermissionId"):
            assert resp.status_code == 201
            assert "rolePermissionId" in resp.json()

    @allure.title("GET /role-permissions — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_role_permissions(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /role-permissions")
        allure.dynamic.tag("smoke", "role-permissions")

        resp = authed_session.get(f"{emp_url}/role-permissions", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /role-permissions/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_role_permissions(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /role-permissions/count")
        allure.dynamic.tag("smoke", "role-permissions")

        resp = authed_session.get(f"{emp_url}/role-permissions/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /role-permissions/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_role_permission_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /role-permissions/{id}")
        allure.dynamic.tag("negative", "role-permissions")

        resp = authed_session.get(f"{emp_url}/role-permissions/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("DELETE /role-permissions/{id} — deletes link, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_role_permission(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /role-permissions/{id}")
        allure.dynamic.tag("smoke", "role-permissions")

        role_id, perm_id = _create_role_and_perm(emp_url, authed_session, auth_headers)
        created = _create_resource(
            emp_url, "role-permissions",
            {"employeeRoleId": role_id, "permissioinsId": perm_id},
            authed_session, auth_headers,
        )
        rp_id = created["rolePermissionId"]

        with allure.step(f"DELETE /role-permissions/{rp_id}"):
            resp = authed_session.delete(f"{emp_url}/role-permissions/{rp_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("POST /role-permissions without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_role_permission_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /role-permissions")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/role-permissions", json={"employeeRoleId": 1, "permissioinsId": 1})
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# OrganizationController — /api/v1/organization
# Fields: parentOrganizationId, organization, description, status  →  organizationId
# ===========================================================================

def _org_payload(tag="org"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    return {
        "parentOrganizationId": None,
        "organization": uid,
        "description": "Test org",
        "status": 1,
    }


@allure.suite("User Service – Reference Data")
@allure.feature("Organization")
@pytest.mark.employee_ref_data
class TestOrganization:

    @allure.title("POST /organization — creates org, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_organization(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /organization")
        allure.dynamic.tag("smoke", "organization")

        with allure.step("POST /organization"):
            resp = authed_session.post(f"{emp_url}/organization", json=_org_payload("smoke"), headers=auth_headers)

        with allure.step("Assert 201 and organizationId"):
            assert resp.status_code == 201
            assert "organizationId" in resp.json()

    @allure.title("GET /organization — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_organizations(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /organization")
        allure.dynamic.tag("smoke", "organization")

        resp = authed_session.get(f"{emp_url}/organization", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /organization/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_organizations(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /organization/count")
        allure.dynamic.tag("smoke", "organization")

        resp = authed_session.get(f"{emp_url}/organization/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("Full CRUD cycle — /organization")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_organization_crud_cycle(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "CRUD /organization")
        allure.dynamic.tag("smoke", "organization")

        _assert_crud(
            emp_url, "organization",
            create_payload=_org_payload("crud"),
            update_payload={**_org_payload("upd"), "description": "Updated"},
            id_field="organizationId",
            authed_session=authed_session,
            auth_headers=auth_headers,
        )

    @allure.title("GET /organization/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_organization_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /organization/{id}")
        allure.dynamic.tag("negative", "organization")

        resp = authed_session.get(f"{emp_url}/organization/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("POST /organization without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_organization_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /organization")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/organization", json=_org_payload("noauth"))
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# ProjectsController — /api/v1/projects
# Fields: project, description, startDate, endDate, status  →  projectId
# ===========================================================================

def _project_payload(tag="proj"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    return {
        "project": uid,
        "description": "Test project",
        "startDate": "2025-01-01",
        "endDate": "2025-12-31",
        "status": 1,
    }


@allure.suite("User Service – Reference Data")
@allure.feature("Projects")
@pytest.mark.employee_ref_data
class TestProjects:

    @allure.title("POST /projects — creates project, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_project(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /projects")
        allure.dynamic.tag("smoke", "projects")

        with allure.step("POST /projects"):
            resp = authed_session.post(f"{emp_url}/projects", json=_project_payload("smoke"), headers=auth_headers)

        with allure.step("Assert 201 and projectId"):
            assert resp.status_code == 201
            assert "projectId" in resp.json()

    @allure.title("GET /projects — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_projects(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /projects")
        allure.dynamic.tag("smoke", "projects")

        resp = authed_session.get(f"{emp_url}/projects", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /projects/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_projects(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /projects/count")
        allure.dynamic.tag("smoke", "projects")

        resp = authed_session.get(f"{emp_url}/projects/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("Full CRUD cycle — /projects")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_crud_cycle(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "CRUD /projects")
        allure.dynamic.tag("smoke", "projects")

        _assert_crud(
            emp_url, "projects",
            create_payload=_project_payload("crud"),
            update_payload={**_project_payload("upd"), "description": "Updated"},
            id_field="projectId",
            authed_session=authed_session,
            auth_headers=auth_headers,
        )

    @allure.title("GET /projects/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_project_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /projects/{id}")
        allure.dynamic.tag("negative", "projects")

        resp = authed_session.get(f"{emp_url}/projects/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("POST /projects without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_project_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /projects")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/projects", json=_project_payload("noauth"))
        assert resp.status_code in (401, 403, 404)
