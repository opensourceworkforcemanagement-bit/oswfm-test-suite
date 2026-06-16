"""
REST API tests for employee contact-info controllers:

  AddressesController      — /api/v1/addresses
  EmailAddressesController — /api/v1/email-addresses
  PhoneNumbersController   — /api/v1/phone-numbers
  EmployeeAddressController— /api/v1/employee-address

Standard CRUD pattern for all:
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
        pytest.skip("No employees available for contact-info tests")
    return employees[0]["employeeId"]


# ===========================================================================
# AddressesController — /api/v1/addresses
# Fields: addressLine1, addressLine2, city, state, zipCode, country, isPrimary
#   →  addressId
# ===========================================================================

def _address_payload():
    return {
        "addressLine1": "123 Main St",
        "addressLine2": "Apt 4B",
        "city": "Anytown",
        "state": "CA",
        "zipCode": "90210",
        "country": "US",
        "isPrimary": True,
    }


@allure.suite("User Service – Contact Info")
@allure.feature("Addresses")
@pytest.mark.employee_contact_info
class TestAddresses:

    @allure.title("POST /addresses — creates address, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_address(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /addresses")
        allure.dynamic.tag("smoke", "addresses")

        with allure.step("POST /addresses with valid payload"):
            resp = authed_session.post(f"{emp_url}/addresses", json=_address_payload(), headers=auth_headers)

        with allure.step("Assert 201 and addressId"):
            assert resp.status_code == 201
            assert "addressId" in resp.json()

    @allure.title("GET /addresses — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_addresses(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /addresses")
        allure.dynamic.tag("smoke", "addresses")

        resp = authed_session.get(f"{emp_url}/addresses", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /addresses/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_addresses(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /addresses/count")
        allure.dynamic.tag("smoke", "addresses")

        resp = authed_session.get(f"{emp_url}/addresses/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /addresses/{id} — returns address for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_address_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /addresses/{id}")
        allure.dynamic.tag("smoke", "addresses")

        created = _create_resource(emp_url, "addresses", _address_payload(), authed_session, auth_headers)
        addr_id = created["addressId"]

        with allure.step(f"GET /addresses/{addr_id}"):
            resp = authed_session.get(f"{emp_url}/addresses/{addr_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching addressId"):
            assert resp.status_code == 200
            assert resp.json()["addressId"] == addr_id

    @allure.title("GET /addresses/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_address_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /addresses/{id}")
        allure.dynamic.tag("negative", "addresses")

        resp = authed_session.get(f"{emp_url}/addresses/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("HEAD /addresses/{id} — 200 for existing, 404 for missing")
    @allure.severity(allure.severity_level.NORMAL)
    def test_head_address(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /addresses/{id}")
        allure.dynamic.tag("smoke", "addresses")

        created = _create_resource(emp_url, "addresses", _address_payload(), authed_session, auth_headers)
        addr_id = created["addressId"]

        assert authed_session.head(f"{emp_url}/addresses/{addr_id}", headers=auth_headers).status_code == 200
        assert authed_session.head(f"{emp_url}/addresses/9999999", headers=auth_headers).status_code == 404

    @allure.title("PUT /addresses/{id} — updates city successfully")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_address(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /addresses/{id}")
        allure.dynamic.tag("smoke", "addresses")

        created = _create_resource(emp_url, "addresses", _address_payload(), authed_session, auth_headers)
        addr_id = created["addressId"]

        with allure.step(f"PUT /addresses/{addr_id} with updated city"):
            payload = {**_address_payload(), "city": "UpdatedCity"}
            resp = authed_session.put(f"{emp_url}/addresses/{addr_id}", json=payload, headers=auth_headers)

        with allure.step("Assert 200 and updated city"):
            assert resp.status_code == 200
            assert resp.json()["city"] == "UpdatedCity"

    @allure.title("DELETE /addresses/{id} — deletes address, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_address(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /addresses/{id}")
        allure.dynamic.tag("smoke", "addresses")

        created = _create_resource(emp_url, "addresses", _address_payload(), authed_session, auth_headers)
        addr_id = created["addressId"]

        with allure.step(f"DELETE /addresses/{addr_id}"):
            resp = authed_session.delete(f"{emp_url}/addresses/{addr_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("DELETE /addresses/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_address_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /addresses/{id}")
        allure.dynamic.tag("negative", "addresses")

        resp = authed_session.delete(f"{emp_url}/addresses/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("POST /addresses without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_address_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /addresses")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/addresses", json=_address_payload())
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# EmailAddressesController — /api/v1/email-addresses
# Fields: employeeId, email, type, isPrimary  →  emailAddressId
# ===========================================================================

def _email_payload(employee_id, tag="email"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    return {
        "employeeId": employee_id,
        "email": f"{uid}@test.com",
        "type": 1,
        "isPrimary": True,
    }


@allure.suite("User Service – Contact Info")
@allure.feature("Email Addresses")
@pytest.mark.employee_contact_info
class TestEmailAddresses:

    @allure.title("POST /email-addresses — creates email address, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_email_address(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /email-addresses")
        allure.dynamic.tag("smoke", "email-addresses")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        payload = _email_payload(employee_id, "smoke")

        with allure.step("POST /email-addresses"):
            resp = authed_session.post(f"{emp_url}/email-addresses", json=payload, headers=auth_headers)

        with allure.step("Assert 201 and emailAddressId"):
            assert resp.status_code == 201
            assert "emailAddressId" in resp.json()

    @allure.title("GET /email-addresses — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_email_addresses(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /email-addresses")
        allure.dynamic.tag("smoke", "email-addresses")

        resp = authed_session.get(f"{emp_url}/email-addresses", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /email-addresses/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_email_addresses(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /email-addresses/count")
        allure.dynamic.tag("smoke", "email-addresses")

        resp = authed_session.get(f"{emp_url}/email-addresses/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /email-addresses/{id} — returns email for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_email_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /email-addresses/{id}")
        allure.dynamic.tag("smoke", "email-addresses")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "email-addresses", _email_payload(employee_id, "getid"), authed_session, auth_headers)
        email_id = created["emailAddressId"]

        with allure.step(f"GET /email-addresses/{email_id}"):
            resp = authed_session.get(f"{emp_url}/email-addresses/{email_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching emailAddressId"):
            assert resp.status_code == 200
            assert resp.json()["emailAddressId"] == email_id

    @allure.title("GET /email-addresses/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_email_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /email-addresses/{id}")
        allure.dynamic.tag("negative", "email-addresses")

        resp = authed_session.get(f"{emp_url}/email-addresses/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("PUT /email-addresses/{id} — updates email")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_email_address(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /email-addresses/{id}")
        allure.dynamic.tag("smoke", "email-addresses")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "email-addresses", _email_payload(employee_id, "upd"), authed_session, auth_headers)
        email_id = created["emailAddressId"]

        new_email = f"updated{int(_time.time() * 1000) % 10_000_000}@test.com"
        payload = {**created, "email": new_email}

        with allure.step(f"PUT /email-addresses/{email_id}"):
            resp = authed_session.put(f"{emp_url}/email-addresses/{email_id}", json=payload, headers=auth_headers)

        with allure.step("Assert 200 and updated email"):
            assert resp.status_code == 200
            assert resp.json()["email"] == new_email

    @allure.title("DELETE /email-addresses/{id} — deletes email, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_email_address(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /email-addresses/{id}")
        allure.dynamic.tag("smoke", "email-addresses")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "email-addresses", _email_payload(employee_id, "del"), authed_session, auth_headers)
        email_id = created["emailAddressId"]

        with allure.step(f"DELETE /email-addresses/{email_id}"):
            resp = authed_session.delete(f"{emp_url}/email-addresses/{email_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("POST /email-addresses without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_email_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /email-addresses")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/email-addresses", json={"employeeId": 1, "email": "x@x.com", "type": 1, "isPrimary": True})
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# PhoneNumbersController — /api/v1/phone-numbers
# Fields: employeeId, phoneNumber, type, isPrimary  →  phoneNumberId
# ===========================================================================

def _phone_payload(employee_id, tag="phone"):
    uid = f"{int(_time.time() * 1000) % 10_000_000}"
    return {
        "employeeId": employee_id,
        "phoneNumber": f"555-{uid[:4]}-{uid[4:]}".ljust(12, "0")[:12],
        "type": 1,
        "isPrimary": True,
    }


@allure.suite("User Service – Contact Info")
@allure.feature("Phone Numbers")
@pytest.mark.employee_contact_info
class TestPhoneNumbers:

    @allure.title("POST /phone-numbers — creates phone number, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_phone_number(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /phone-numbers")
        allure.dynamic.tag("smoke", "phone-numbers")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)

        with allure.step("POST /phone-numbers"):
            resp = authed_session.post(f"{emp_url}/phone-numbers", json=_phone_payload(employee_id), headers=auth_headers)

        with allure.step("Assert 201 and phoneNumberId"):
            assert resp.status_code == 201
            assert "phoneNumberId" in resp.json()

    @allure.title("GET /phone-numbers — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_phone_numbers(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /phone-numbers")
        allure.dynamic.tag("smoke", "phone-numbers")

        resp = authed_session.get(f"{emp_url}/phone-numbers", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /phone-numbers/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_phone_numbers(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /phone-numbers/count")
        allure.dynamic.tag("smoke", "phone-numbers")

        resp = authed_session.get(f"{emp_url}/phone-numbers/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /phone-numbers/{id} — returns phone for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_phone_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /phone-numbers/{id}")
        allure.dynamic.tag("smoke", "phone-numbers")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "phone-numbers", _phone_payload(employee_id), authed_session, auth_headers)
        phone_id = created["phoneNumberId"]

        with allure.step(f"GET /phone-numbers/{phone_id}"):
            resp = authed_session.get(f"{emp_url}/phone-numbers/{phone_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching phoneNumberId"):
            assert resp.status_code == 200
            assert resp.json()["phoneNumberId"] == phone_id

    @allure.title("GET /phone-numbers/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_phone_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /phone-numbers/{id}")
        allure.dynamic.tag("negative", "phone-numbers")

        resp = authed_session.get(f"{emp_url}/phone-numbers/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("HEAD /phone-numbers/{id} — 200 for existing, 404 for missing")
    @allure.severity(allure.severity_level.NORMAL)
    def test_head_phone_number(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /phone-numbers/{id}")
        allure.dynamic.tag("smoke", "phone-numbers")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "phone-numbers", _phone_payload(employee_id), authed_session, auth_headers)
        phone_id = created["phoneNumberId"]

        assert authed_session.head(f"{emp_url}/phone-numbers/{phone_id}", headers=auth_headers).status_code == 200
        assert authed_session.head(f"{emp_url}/phone-numbers/9999999", headers=auth_headers).status_code == 404

    @allure.title("PUT /phone-numbers/{id} — updates phone number")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_phone_number(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /phone-numbers/{id}")
        allure.dynamic.tag("smoke", "phone-numbers")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "phone-numbers", _phone_payload(employee_id), authed_session, auth_headers)
        phone_id = created["phoneNumberId"]

        with allure.step(f"PUT /phone-numbers/{phone_id}"):
            payload = {**created, "phoneNumber": "555-000-0001"}
            resp = authed_session.put(f"{emp_url}/phone-numbers/{phone_id}", json=payload, headers=auth_headers)

        with allure.step("Assert 200 and updated phoneNumber"):
            assert resp.status_code == 200
            assert resp.json()["phoneNumber"] == "555-000-0001"

    @allure.title("DELETE /phone-numbers/{id} — deletes phone, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_phone_number(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /phone-numbers/{id}")
        allure.dynamic.tag("smoke", "phone-numbers")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(emp_url, "phone-numbers", _phone_payload(employee_id), authed_session, auth_headers)
        phone_id = created["phoneNumberId"]

        with allure.step(f"DELETE /phone-numbers/{phone_id}"):
            resp = authed_session.delete(f"{emp_url}/phone-numbers/{phone_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("POST /phone-numbers without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_phone_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /phone-numbers")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/phone-numbers", json={"employeeId": 1, "phoneNumber": "555-0000", "type": 1, "isPrimary": True})
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# EmployeeAddressController — /api/v1/employee-address
# Fields: employeeId  (addressId stored as FK)  →  addressId + employeeId
# Note: EmployeeAddressRequestDTO only carries employeeId; the addressId
#       comes from the path or auto-resolution. Adjust if entity differs.
# ===========================================================================

def _emp_address_payload(employee_id, address_id):
    return {"employeeId": employee_id, "addressId": address_id}


@allure.suite("User Service – Contact Info")
@allure.feature("Employee Address")
@pytest.mark.employee_contact_info
class TestEmployeeAddress:

    @allure.title("POST /employee-address — links employee to address, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_employee_address(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employee-address")
        allure.dynamic.tag("smoke", "employee-address")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        address = _create_resource(emp_url, "addresses", _address_payload(), authed_session, auth_headers)
        address_id = address["addressId"]
        payload = _emp_address_payload(employee_id, address_id)

        with allure.step("POST /employee-address"):
            resp = authed_session.post(f"{emp_url}/employee-address", json=payload, headers=auth_headers)

        with allure.step("Assert 201"):
            assert resp.status_code == 201

    @allure.title("GET /employee-address — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_employee_addresses(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employee-address")
        allure.dynamic.tag("smoke", "employee-address")

        resp = authed_session.get(f"{emp_url}/employee-address", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /employee-address/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_employee_addresses(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employee-address/count")
        allure.dynamic.tag("smoke", "employee-address")

        resp = authed_session.get(f"{emp_url}/employee-address/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /employee-address/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_employee_address_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employee-address/{id}")
        allure.dynamic.tag("negative", "employee-address")

        resp = authed_session.get(f"{emp_url}/employee-address/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("HEAD /employee-address/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.MINOR)
    def test_head_employee_address_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /employee-address/{id}")
        allure.dynamic.tag("negative", "employee-address")

        resp = authed_session.head(f"{emp_url}/employee-address/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("DELETE /employee-address/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_employee_address_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employee-address/{id}")
        allure.dynamic.tag("negative", "employee-address")

        resp = authed_session.delete(f"{emp_url}/employee-address/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("GET /employee-address/{id} — returns link for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_employee_address_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employee-address/{id}")
        allure.dynamic.tag("smoke", "employee-address")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        address = _create_resource(emp_url, "addresses", _address_payload(), authed_session, auth_headers)
        address_id = address["addressId"]
        created = _create_resource(
            emp_url, "employee-address",
            _emp_address_payload(employee_id, address_id),
            authed_session, auth_headers,
        )

        link_id = created.get("addressId") or created.get("id")
        if link_id is None:
            pytest.skip("Cannot determine link id from response")

        with allure.step(f"GET /employee-address/{link_id}"):
            resp = authed_session.get(f"{emp_url}/employee-address/{link_id}", headers=auth_headers)

        with allure.step("Assert 200"):
            assert resp.status_code == 200

    @allure.title("DELETE /employee-address/{id} — deletes link, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_employee_address(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employee-address/{id}")
        allure.dynamic.tag("smoke", "employee-address")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        address = _create_resource(emp_url, "addresses", _address_payload(), authed_session, auth_headers)
        address_id = address["addressId"]
        created = _create_resource(
            emp_url, "employee-address",
            _emp_address_payload(employee_id, address_id),
            authed_session, auth_headers,
        )

        link_id = created.get("addressId") or created.get("id")
        if link_id is None:
            pytest.skip("Cannot determine link id from response")

        with allure.step(f"DELETE /employee-address/{link_id}"):
            resp = authed_session.delete(f"{emp_url}/employee-address/{link_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("POST /employee-address without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_employee_address_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employee-address")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(f"{emp_url}/employee-address", json={"employeeId": 1, "addressId": 1})
        assert resp.status_code in (401, 403, 404)


# Re-export _address_payload so other test modules can import it without
# duplicating the definition (used by employee-address tests above).
def _address_payload():
    return {
        "addressLine1": "123 Main St",
        "addressLine2": "Apt 4B",
        "city": "Anytown",
        "state": "CA",
        "zipCode": "90210",
        "country": "US",
        "isPrimary": True,
    }
