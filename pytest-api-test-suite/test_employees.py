"""
REST API tests for EmployeesController and EmployeeUserController.

EmployeesController  — /api/v1/employees
  POST   /create
  POST   /create-with-user
  GET    /
  GET    /count
  GET    /{id}
  HEAD   /{id}
  PUT    /{id}
  DELETE /{id}

EmployeeUserController — /api/v1/employee-user
  POST   /
  GET    /
  GET    /count
  GET    /{id}
  HEAD   /{id}
  GET    /employee/{employeeId}
  GET    /user/{userId}
  PUT    /{id}
  DELETE /{id}

NOTE: /api/v1/employee-user is not yet wired in GatewayConfig — tests target
the gateway URL so they will 404/502 until the route is added.
"""

import time as _time
import allure
import pytest
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_employee_payload(tag="emp"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    return {
        "employeeIdentifier": uid,
        "firstName": "Api",
        "middleName": "",
        "lastName": "Tester",
        "status": 1,
        "userName": uid,
    }


def _create_employee(emp_url, authed_session, auth_headers, tag="emp"):
    payload = _fresh_employee_payload(tag)
    resp = authed_session.post(f"{emp_url}/employees/create", json=payload, headers=auth_headers)
    if resp.status_code != 201:
        pytest.skip(f"Could not create employee for test: {resp.status_code} {resp.text[:200]}")
    return resp.json()["employeeId"], payload


# ---------------------------------------------------------------------------
# POST /employees/create
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employees")
@allure.feature("Create Employee")
@pytest.mark.employees
class TestCreateEmployee:

    @allure.title("POST /employees/create — happy path returns 201 and employeeId")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_employee_success(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees/create")
        allure.dynamic.tag("smoke", "employees")

        payload = _fresh_employee_payload("smoke")

        with allure.step("POST /employees/create with valid payload"):
            resp = authed_session.post(f"{emp_url}/employees/create", json=payload, headers=auth_headers)

        with allure.step("Assert 201 and employeeId present"):
            assert resp.status_code == 201
            body = resp.json()
            assert "employeeId" in body
            assert body["firstName"] == payload["firstName"]
            assert body["lastName"] == payload["lastName"]

    @allure.title("POST /employees/create without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_employee_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees/create")
        allure.dynamic.tag("negative", "auth")

        with allure.step("POST /employees/create without Authorization header"):
            resp = requests.post(f"{emp_url}/employees/create", json=_fresh_employee_payload("noauth"))

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)

    @allure.title("POST /employees/create with missing firstName — validation error")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_employee_missing_first_name(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees/create")
        allure.dynamic.tag("negative", "validation")

        payload = {k: v for k, v in _fresh_employee_payload("miss").items() if k != "firstName"}

        with allure.step("POST /employees/create without firstName"):
            resp = authed_session.post(f"{emp_url}/employees/create", json=payload, headers=auth_headers)

        with allure.step("Assert 400 or non-2xx"):
            assert resp.status_code >= 400


# ---------------------------------------------------------------------------
# POST /employees/create-with-user
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employees")
@allure.feature("Create Employee With User")
@pytest.mark.employees
class TestCreateEmployeeWithUser:

    @allure.title("POST /employees/create-with-user — createUser=false creates employee only")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_with_user_no_user(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees/create-with-user")
        allure.dynamic.tag("smoke", "employees")

        uid = f"cwu{int(_time.time() * 1000) % 10_000_000}"
        payload = {
            "employeeIdentifier": uid,
            "firstName": "Create",
            "middleName": "",
            "lastName": "WithUser",
            "status": 1,
            "userName": uid,
            "createUser": False,
            "password": None,
        }

        with allure.step("POST /employees/create-with-user with createUser=false"):
            resp = authed_session.post(f"{emp_url}/employees/create-with-user", json=payload, headers=auth_headers)

        with allure.step("Assert 201 and employeeId present"):
            assert resp.status_code == 201
            body = resp.json()
            assert "employeeId" in body

    @allure.title("POST /employees/create-with-user — duplicate userName returns 409")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_with_user_duplicate_username(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees/create-with-user")
        allure.dynamic.tag("negative", "employees")

        uid = f"dup{int(_time.time() * 1000) % 10_000_000}"
        payload = {
            "employeeIdentifier": uid,
            "firstName": "Dup",
            "middleName": "",
            "lastName": "User",
            "status": 1,
            "userName": uid,
            "createUser": True,
            "password": "Jk#9mWpL@2vN",
        }

        with allure.step("Create employee+user once"):
            first = authed_session.post(f"{emp_url}/employees/create-with-user", json=payload, headers=auth_headers)
            if first.status_code != 201:
                pytest.skip(f"Initial creation failed: {first.status_code} {first.text[:200]}")

        with allure.step("Attempt to create the same userName again"):
            resp = authed_session.post(f"{emp_url}/employees/create-with-user", json=payload, headers=auth_headers)

        with allure.step("Assert 409 Conflict"):
            assert resp.status_code == 409

    @allure.title("POST /employees/create-with-user without auth — unauthorized")
    @allure.severity(allure.severity_level.MINOR)
    def test_create_with_user_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees/create-with-user")
        allure.dynamic.tag("negative", "auth")

        with allure.step("POST /employees/create-with-user without auth"):
            resp = requests.post(f"{emp_url}/employees/create-with-user", json={})

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ---------------------------------------------------------------------------
# GET /employees  — list all
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employees")
@allure.feature("Get All Employees")
@pytest.mark.employees
class TestGetAllEmployees:

    @allure.title("GET /employees — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_employees(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees")
        allure.dynamic.tag("smoke", "employees")

        with allure.step("GET /employees"):
            resp = authed_session.get(f"{emp_url}/employees", headers=auth_headers)

        with allure.step("Assert 200 and list"):
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)

    @allure.title("GET /employees without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_employees_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "GET /employees")
        allure.dynamic.tag("negative", "auth")

        with allure.step("GET /employees without auth"):
            resp = requests.get(f"{emp_url}/employees")

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ---------------------------------------------------------------------------
# GET /employees/count
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employees")
@allure.feature("Count Employees")
@pytest.mark.employees
class TestCountEmployees:

    @allure.title("GET /employees/count — returns numeric count")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_employees(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees/count")
        allure.dynamic.tag("smoke", "employees")

        with allure.step("GET /employees/count"):
            resp = authed_session.get(f"{emp_url}/employees/count", headers=auth_headers)

        with allure.step("Assert 200 and integer body"):
            assert resp.status_code == 200
            assert isinstance(resp.json(), int)


# ---------------------------------------------------------------------------
# GET /employees/{id}
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employees")
@allure.feature("Get Employee By ID")
@pytest.mark.employees
class TestGetEmployeeById:

    @allure.title("GET /employees/{id} — returns employee for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_by_id_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees/{id}")
        allure.dynamic.tag("smoke", "employees")

        employee_id, _ = _create_employee(emp_url, authed_session, auth_headers, "getbyid")

        with allure.step(f"GET /employees/{employee_id}"):
            resp = authed_session.get(f"{emp_url}/employees/{employee_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching employeeId"):
            assert resp.status_code == 200
            assert resp.json()["employeeId"] == employee_id

    @allure.title("GET /employees/{id} — non-existent id returns 404")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_by_id_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees/{id}")
        allure.dynamic.tag("negative", "employees")

        with allure.step("GET /employees/9999999"):
            resp = authed_session.get(f"{emp_url}/employees/9999999", headers=auth_headers)

        with allure.step("Assert 404"):
            assert resp.status_code == 404

    @allure.title("GET /employees/{id} without auth — unauthorized")
    @allure.severity(allure.severity_level.MINOR)
    def test_get_by_id_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "GET /employees/{id}")
        allure.dynamic.tag("negative", "auth")

        with allure.step("GET /employees/1 without auth"):
            resp = requests.get(f"{emp_url}/employees/1")

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ---------------------------------------------------------------------------
# HEAD /employees/{id}
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employees")
@allure.feature("Employee Exists")
@pytest.mark.employees
class TestEmployeeExists:

    @allure.title("HEAD /employees/{id} — 200 for existing employee")
    @allure.severity(allure.severity_level.NORMAL)
    def test_head_exists(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /employees/{id}")
        allure.dynamic.tag("smoke", "employees")

        employee_id, _ = _create_employee(emp_url, authed_session, auth_headers, "head")

        with allure.step(f"HEAD /employees/{employee_id}"):
            resp = authed_session.head(f"{emp_url}/employees/{employee_id}", headers=auth_headers)

        with allure.step("Assert 200"):
            assert resp.status_code == 200

    @allure.title("HEAD /employees/{id} — 404 for non-existent employee")
    @allure.severity(allure.severity_level.MINOR)
    def test_head_not_exists(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /employees/{id}")
        allure.dynamic.tag("negative", "employees")

        with allure.step("HEAD /employees/9999999"):
            resp = authed_session.head(f"{emp_url}/employees/9999999", headers=auth_headers)

        with allure.step("Assert 404"):
            assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /employees/{id}
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employees")
@allure.feature("Update Employee")
@pytest.mark.employees
class TestUpdateEmployee:

    @allure.title("PUT /employees/{id} — updates firstName successfully")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_employee_success(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /employees/{id}")
        allure.dynamic.tag("smoke", "employees")

        employee_id, original = _create_employee(emp_url, authed_session, auth_headers, "upd")

        with allure.step(f"PUT /employees/{employee_id} with updated firstName"):
            payload = {**original, "firstName": "Updated"}
            resp = authed_session.put(f"{emp_url}/employees/{employee_id}", json=payload, headers=auth_headers)

        with allure.step("Assert 200 and updated firstName"):
            assert resp.status_code == 200
            assert resp.json()["firstName"] == "Updated"

    @allure.title("PUT /employees/{id} — non-existent id returns 404")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_employee_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /employees/{id}")
        allure.dynamic.tag("negative", "employees")

        payload = {"employeeIdentifier": "ghost", "firstName": "Ghost", "lastName": "Emp", "status": 1, "userName": "ghost"}

        with allure.step("PUT /employees/9999999 with dummy payload"):
            resp = authed_session.put(f"{emp_url}/employees/9999999", json=payload, headers=auth_headers)

        with allure.step("Assert 404"):
            assert resp.status_code == 404

    @allure.title("PUT /employees/{id} without auth — unauthorized")
    @allure.severity(allure.severity_level.MINOR)
    def test_update_employee_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "PUT /employees/{id}")
        allure.dynamic.tag("negative", "auth")

        with allure.step("PUT /employees/1 without auth"):
            resp = requests.put(f"{emp_url}/employees/1", json={"firstName": "X"})

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ---------------------------------------------------------------------------
# DELETE /employees/{id}
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employees")
@allure.feature("Delete Employee")
@pytest.mark.employees
class TestDeleteEmployee:

    @allure.title("DELETE /employees/{id} — deletes a freshly created employee")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_employee_success(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees/{id}")
        allure.dynamic.tag("smoke", "employees")

        employee_id, _ = _create_employee(emp_url, authed_session, auth_headers, "del")

        with allure.step(f"DELETE /employees/{employee_id}"):
            resp = authed_session.delete(f"{emp_url}/employees/{employee_id}", headers=auth_headers)

        with allure.step("Assert 204 No Content"):
            assert resp.status_code == 204

    @allure.title("DELETE /employees/{id} — non-existent id returns 404")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_employee_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees/{id}")
        allure.dynamic.tag("negative", "employees")

        with allure.step("DELETE /employees/9999999"):
            resp = authed_session.delete(f"{emp_url}/employees/9999999", headers=auth_headers)

        with allure.step("Assert 404"):
            assert resp.status_code == 404

    @allure.title("DELETE /employees/{id} without auth — unauthorized")
    @allure.severity(allure.severity_level.MINOR)
    def test_delete_employee_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "DELETE /employees/{id}")
        allure.dynamic.tag("negative", "auth")

        with allure.step("DELETE /employees/1 without auth"):
            resp = requests.delete(f"{emp_url}/employees/1")

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ===========================================================================
# EmployeeUserController  — /api/v1/employee-user
# NOTE: this route is not yet registered in GatewayConfig; tests will fail
# with 404 until the gateway route is added.
# ===========================================================================

def _create_employee_user(emp_url, authed_session, auth_headers, employee_id, user_id):
    payload = {"employeeId": employee_id, "userId": user_id}
    resp = authed_session.post(f"{emp_url}/employee-user", json=payload, headers=auth_headers)
    if resp.status_code != 201:
        pytest.skip(f"Could not create employee-user link: {resp.status_code} {resp.text[:200]}")
    return resp.json()["employeeUserId"]


# ---------------------------------------------------------------------------
# POST /employee-user
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employee User")
@allure.feature("Create Employee User")
@pytest.mark.employee_user
class TestCreateEmployeeUser:

    @allure.title("POST /employee-user — creates link between employee and user")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_employee_user_success(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employee-user")
        allure.dynamic.tag("smoke", "employee-user")

        employee_id, _ = _create_employee(emp_url, authed_session, auth_headers, "eu")
        # Use a placeholder userId; actual value depends on what's in the DB.
        # If FK constraints are enforced this test requires a real userId.
        payload = {"employeeId": employee_id, "userId": 1}

        with allure.step("POST /employee-user with employeeId and userId"):
            resp = authed_session.post(f"{emp_url}/employee-user", json=payload, headers=auth_headers)

        with allure.step("Assert 201 and employeeUserId present"):
            assert resp.status_code == 201
            body = resp.json()
            assert "employeeUserId" in body

    @allure.title("POST /employee-user without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_employee_user_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employee-user")
        allure.dynamic.tag("negative", "auth")

        with allure.step("POST /employee-user without auth"):
            resp = requests.post(f"{emp_url}/employee-user", json={"employeeId": 1, "userId": 1})

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ---------------------------------------------------------------------------
# GET /employee-user
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employee User")
@allure.feature("Get All Employee Users")
@pytest.mark.employee_user
class TestGetAllEmployeeUsers:

    @allure.title("GET /employee-user — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_employee_users(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employee-user")
        allure.dynamic.tag("smoke", "employee-user")

        with allure.step("GET /employee-user"):
            resp = authed_session.get(f"{emp_url}/employee-user", headers=auth_headers)

        with allure.step("Assert 200 and list"):
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)

    @allure.title("GET /employee-user without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_all_employee_users_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "GET /employee-user")
        allure.dynamic.tag("negative", "auth")

        with allure.step("GET /employee-user without auth"):
            resp = requests.get(f"{emp_url}/employee-user")

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ---------------------------------------------------------------------------
# GET /employee-user/count
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employee User")
@allure.feature("Count Employee Users")
@pytest.mark.employee_user
class TestCountEmployeeUsers:

    @allure.title("GET /employee-user/count — returns numeric count")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_employee_users(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employee-user/count")
        allure.dynamic.tag("smoke", "employee-user")

        with allure.step("GET /employee-user/count"):
            resp = authed_session.get(f"{emp_url}/employee-user/count", headers=auth_headers)

        with allure.step("Assert 200 and integer body"):
            assert resp.status_code == 200
            assert isinstance(resp.json(), int)


# ---------------------------------------------------------------------------
# GET /employee-user/{id}
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employee User")
@allure.feature("Get Employee User By ID")
@pytest.mark.employee_user
class TestGetEmployeeUserById:

    @allure.title("GET /employee-user/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_by_id_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employee-user/{id}")
        allure.dynamic.tag("negative", "employee-user")

        with allure.step("GET /employee-user/9999999"):
            resp = authed_session.get(f"{emp_url}/employee-user/9999999", headers=auth_headers)

        with allure.step("Assert 404"):
            assert resp.status_code == 404

    @allure.title("GET /employee-user/{id} without auth — unauthorized")
    @allure.severity(allure.severity_level.MINOR)
    def test_get_by_id_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "GET /employee-user/{id}")
        allure.dynamic.tag("negative", "auth")

        with allure.step("GET /employee-user/1 without auth"):
            resp = requests.get(f"{emp_url}/employee-user/1")

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ---------------------------------------------------------------------------
# HEAD /employee-user/{id}
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employee User")
@allure.feature("Employee User Exists")
@pytest.mark.employee_user
class TestEmployeeUserExists:

    @allure.title("HEAD /employee-user/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.MINOR)
    def test_head_not_exists(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /employee-user/{id}")
        allure.dynamic.tag("negative", "employee-user")

        with allure.step("HEAD /employee-user/9999999"):
            resp = authed_session.head(f"{emp_url}/employee-user/9999999", headers=auth_headers)

        with allure.step("Assert 404"):
            assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /employee-user/employee/{employeeId}
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employee User")
@allure.feature("Get Employee Users By Employee ID")
@pytest.mark.employee_user
class TestGetByEmployeeId:

    @allure.title("GET /employee-user/employee/{employeeId} — returns list for any employeeId")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_by_employee_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employee-user/employee/{employeeId}")
        allure.dynamic.tag("smoke", "employee-user")

        employee_id, _ = _create_employee(emp_url, authed_session, auth_headers, "byemp")

        with allure.step(f"GET /employee-user/employee/{employee_id}"):
            resp = authed_session.get(f"{emp_url}/employee-user/employee/{employee_id}", headers=auth_headers)

        with allure.step("Assert 200 and list"):
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)

    @allure.title("GET /employee-user/employee/{employeeId} without auth — unauthorized")
    @allure.severity(allure.severity_level.MINOR)
    def test_get_by_employee_id_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "GET /employee-user/employee/{employeeId}")
        allure.dynamic.tag("negative", "auth")

        with allure.step("GET /employee-user/employee/1 without auth"):
            resp = requests.get(f"{emp_url}/employee-user/employee/1")

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ---------------------------------------------------------------------------
# GET /employee-user/user/{userId}
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employee User")
@allure.feature("Get Employee Users By User ID")
@pytest.mark.employee_user
class TestGetByUserId:

    @allure.title("GET /employee-user/user/{userId} — returns list for any userId")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_by_user_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employee-user/user/{userId}")
        allure.dynamic.tag("smoke", "employee-user")

        with allure.step("GET /employee-user/user/1"):
            resp = authed_session.get(f"{emp_url}/employee-user/user/1", headers=auth_headers)

        with allure.step("Assert 200 and list"):
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)

    @allure.title("GET /employee-user/user/{userId} without auth — unauthorized")
    @allure.severity(allure.severity_level.MINOR)
    def test_get_by_user_id_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "GET /employee-user/user/{userId}")
        allure.dynamic.tag("negative", "auth")

        with allure.step("GET /employee-user/user/1 without auth"):
            resp = requests.get(f"{emp_url}/employee-user/user/1")

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ---------------------------------------------------------------------------
# PUT /employee-user/{id}
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employee User")
@allure.feature("Update Employee User")
@pytest.mark.employee_user
class TestUpdateEmployeeUser:

    @allure.title("PUT /employee-user/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /employee-user/{id}")
        allure.dynamic.tag("negative", "employee-user")

        with allure.step("PUT /employee-user/9999999 with dummy payload"):
            resp = authed_session.put(
                f"{emp_url}/employee-user/9999999",
                json={"employeeId": 1, "userId": 1},
                headers=auth_headers,
            )

        with allure.step("Assert 404"):
            assert resp.status_code == 404

    @allure.title("PUT /employee-user/{id} without auth — unauthorized")
    @allure.severity(allure.severity_level.MINOR)
    def test_update_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "PUT /employee-user/{id}")
        allure.dynamic.tag("negative", "auth")

        with allure.step("PUT /employee-user/1 without auth"):
            resp = requests.put(f"{emp_url}/employee-user/1", json={"employeeId": 1, "userId": 1})

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)


# ---------------------------------------------------------------------------
# DELETE /employee-user/{id}
# ---------------------------------------------------------------------------

@allure.suite("User Service – Employee User")
@allure.feature("Delete Employee User")
@pytest.mark.employee_user
class TestDeleteEmployeeUser:

    @allure.title("DELETE /employee-user/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employee-user/{id}")
        allure.dynamic.tag("negative", "employee-user")

        with allure.step("DELETE /employee-user/9999999"):
            resp = authed_session.delete(f"{emp_url}/employee-user/9999999", headers=auth_headers)

        with allure.step("Assert 404"):
            assert resp.status_code == 404

    @allure.title("DELETE /employee-user/{id} without auth — unauthorized")
    @allure.severity(allure.severity_level.MINOR)
    def test_delete_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "DELETE /employee-user/{id}")
        allure.dynamic.tag("negative", "auth")

        with allure.step("DELETE /employee-user/1 without auth"):
            resp = requests.delete(f"{emp_url}/employee-user/1")

        with allure.step("Assert 401, 403 or 404"):
            assert resp.status_code in (401, 403, 404)
