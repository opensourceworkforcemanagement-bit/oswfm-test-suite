"""
REST API tests for employee emergency-contact controllers:

  EmployeesEmergencyContactsController      — /api/v1/employees-emergency-contacts
  EmployeesEmergencyContactEmailsController — /api/v1/employees-emergency-contact-emails
  EmployeesEmergencyContactPhoneNumbersController
                                            — /api/v1/employees-emergency-contact-phone-numbers

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
        pytest.skip("No employees available for emergency-contact tests")
    return employees[0]["employeeId"]


def _create_emergency_contact(emp_url, authed_session, auth_headers, employee_id, tag="ec"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    payload = {
        "employeeId": employee_id,
        "firstName": "Emergency",
        "middleName": "",
        "lastName": uid,
        "relationship": "Spouse",
    }
    return _create_resource(emp_url, "employees-emergency-contacts", payload, authed_session, auth_headers)


# ===========================================================================
# EmployeesEmergencyContactsController — /api/v1/employees-emergency-contacts
# Fields: employeeId, firstName, middleName, lastName, relationship
#   →  emergencyContactId
# ===========================================================================

def _contact_payload(employee_id, tag="ec"):
    uid = f"{tag}{int(_time.time() * 1000) % 10_000_000}"
    return {
        "employeeId": employee_id,
        "firstName": "Emergency",
        "middleName": "",
        "lastName": uid,
        "relationship": "Parent",
    }


@allure.suite("User Service – Emergency Contacts")
@allure.feature("Employees Emergency Contacts")
@pytest.mark.employee_emergency_contacts
class TestEmployeesEmergencyContacts:

    @allure.title("POST /employees-emergency-contacts — creates contact, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_emergency_contact(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees-emergency-contacts")
        allure.dynamic.tag("smoke", "emergency-contacts")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        payload = _contact_payload(employee_id, "smoke")

        with allure.step("POST /employees-emergency-contacts"):
            resp = authed_session.post(f"{emp_url}/employees-emergency-contacts", json=payload, headers=auth_headers)

        with allure.step("Assert 201 and emergencyContactId"):
            assert resp.status_code == 201
            body = resp.json()
            assert "emergencyContactId" in body
            assert body["employeeId"] == employee_id

    @allure.title("GET /employees-emergency-contacts — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_emergency_contacts(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contacts")
        allure.dynamic.tag("smoke", "emergency-contacts")

        resp = authed_session.get(f"{emp_url}/employees-emergency-contacts", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /employees-emergency-contacts/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_emergency_contacts(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contacts/count")
        allure.dynamic.tag("smoke", "emergency-contacts")

        resp = authed_session.get(f"{emp_url}/employees-emergency-contacts/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /employees-emergency-contacts/{id} — returns contact for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_emergency_contact_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contacts/{id}")
        allure.dynamic.tag("smoke", "emergency-contacts")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(
            emp_url, "employees-emergency-contacts",
            _contact_payload(employee_id, "getid"),
            authed_session, auth_headers,
        )
        contact_id = created["emergencyContactId"]

        with allure.step(f"GET /employees-emergency-contacts/{contact_id}"):
            resp = authed_session.get(f"{emp_url}/employees-emergency-contacts/{contact_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching emergencyContactId"):
            assert resp.status_code == 200
            assert resp.json()["emergencyContactId"] == contact_id

    @allure.title("GET /employees-emergency-contacts/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_emergency_contact_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contacts/{id}")
        allure.dynamic.tag("negative", "emergency-contacts")

        resp = authed_session.get(f"{emp_url}/employees-emergency-contacts/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("HEAD /employees-emergency-contacts/{id} — 200 for existing, 404 for missing")
    @allure.severity(allure.severity_level.NORMAL)
    def test_head_emergency_contact(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "HEAD /employees-emergency-contacts/{id}")
        allure.dynamic.tag("smoke", "emergency-contacts")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(
            emp_url, "employees-emergency-contacts",
            _contact_payload(employee_id, "head"),
            authed_session, auth_headers,
        )
        contact_id = created["emergencyContactId"]

        assert authed_session.head(f"{emp_url}/employees-emergency-contacts/{contact_id}", headers=auth_headers).status_code == 200
        assert authed_session.head(f"{emp_url}/employees-emergency-contacts/9999999", headers=auth_headers).status_code == 404

    @allure.title("PUT /employees-emergency-contacts/{id} — updates relationship")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_update_emergency_contact(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "PUT /employees-emergency-contacts/{id}")
        allure.dynamic.tag("smoke", "emergency-contacts")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(
            emp_url, "employees-emergency-contacts",
            _contact_payload(employee_id, "upd"),
            authed_session, auth_headers,
        )
        contact_id = created["emergencyContactId"]

        with allure.step(f"PUT /employees-emergency-contacts/{contact_id}"):
            payload = {**created, "relationship": "Sibling"}
            resp = authed_session.put(
                f"{emp_url}/employees-emergency-contacts/{contact_id}",
                json=payload,
                headers=auth_headers,
            )

        with allure.step("Assert 200 and updated relationship"):
            assert resp.status_code == 200
            assert resp.json()["relationship"] == "Sibling"

    @allure.title("DELETE /employees-emergency-contacts/{id} — deletes contact, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_emergency_contact(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-emergency-contacts/{id}")
        allure.dynamic.tag("smoke", "emergency-contacts")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        created = _create_resource(
            emp_url, "employees-emergency-contacts",
            _contact_payload(employee_id, "del"),
            authed_session, auth_headers,
        )
        contact_id = created["emergencyContactId"]

        with allure.step(f"DELETE /employees-emergency-contacts/{contact_id}"):
            resp = authed_session.delete(f"{emp_url}/employees-emergency-contacts/{contact_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("DELETE /employees-emergency-contacts/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_emergency_contact_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-emergency-contacts/{id}")
        allure.dynamic.tag("negative", "emergency-contacts")

        resp = authed_session.delete(f"{emp_url}/employees-emergency-contacts/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("POST /employees-emergency-contacts without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_emergency_contact_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees-emergency-contacts")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(
            f"{emp_url}/employees-emergency-contacts",
            json={"employeeId": 1, "firstName": "X", "lastName": "Y", "relationship": "Z"},
        )
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# EmployeesEmergencyContactEmailsController
#   — /api/v1/employees-emergency-contact-emails
# Fields: emergencyContactId, emailAddressId  →  emergencyContactEmailId
# ===========================================================================

def _contact_email_payload(contact_id, email_address_id):
    return {
        "emergencyContactId": contact_id,
        "emailAddressId": email_address_id,
    }


def _create_email_address_for_employee(emp_url, authed_session, auth_headers, employee_id):
    uid = f"ec{int(_time.time() * 1000) % 10_000_000}"
    payload = {
        "employeeId": employee_id,
        "email": f"{uid}@ec.test.com",
        "type": 1,
        "isPrimary": False,
    }
    return _create_resource(emp_url, "email-addresses", payload, authed_session, auth_headers)


@allure.suite("User Service – Emergency Contacts")
@allure.feature("Emergency Contact Emails")
@pytest.mark.employee_emergency_contacts
class TestEmergencyContactEmails:

    @allure.title("POST /employees-emergency-contact-emails — creates link, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_emergency_contact_email(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees-emergency-contact-emails")
        allure.dynamic.tag("smoke", "emergency-contact-emails")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        contact = _create_emergency_contact(emp_url, authed_session, auth_headers, employee_id, "ece")
        email = _create_email_address_for_employee(emp_url, authed_session, auth_headers, employee_id)
        payload = _contact_email_payload(contact["emergencyContactId"], email["emailAddressId"])

        with allure.step("POST /employees-emergency-contact-emails"):
            resp = authed_session.post(
                f"{emp_url}/employees-emergency-contact-emails",
                json=payload,
                headers=auth_headers,
            )

        with allure.step("Assert 201 and emergencyContactEmailId"):
            assert resp.status_code == 201
            assert "emergencyContactEmailId" in resp.json()

    @allure.title("GET /employees-emergency-contact-emails — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_emergency_contact_emails(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contact-emails")
        allure.dynamic.tag("smoke", "emergency-contact-emails")

        resp = authed_session.get(f"{emp_url}/employees-emergency-contact-emails", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /employees-emergency-contact-emails/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_emergency_contact_emails(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contact-emails/count")
        allure.dynamic.tag("smoke", "emergency-contact-emails")

        resp = authed_session.get(f"{emp_url}/employees-emergency-contact-emails/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /employees-emergency-contact-emails/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_emergency_contact_email_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contact-emails/{id}")
        allure.dynamic.tag("negative", "emergency-contact-emails")

        resp = authed_session.get(f"{emp_url}/employees-emergency-contact-emails/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("GET /employees-emergency-contact-emails/{id} — returns link for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_emergency_contact_email_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contact-emails/{id}")
        allure.dynamic.tag("smoke", "emergency-contact-emails")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        contact = _create_emergency_contact(emp_url, authed_session, auth_headers, employee_id, "eceid")
        email = _create_email_address_for_employee(emp_url, authed_session, auth_headers, employee_id)
        created = _create_resource(
            emp_url, "employees-emergency-contact-emails",
            _contact_email_payload(contact["emergencyContactId"], email["emailAddressId"]),
            authed_session, auth_headers,
        )
        link_id = created["emergencyContactEmailId"]

        with allure.step(f"GET /employees-emergency-contact-emails/{link_id}"):
            resp = authed_session.get(f"{emp_url}/employees-emergency-contact-emails/{link_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching id"):
            assert resp.status_code == 200
            assert resp.json()["emergencyContactEmailId"] == link_id

    @allure.title("DELETE /employees-emergency-contact-emails/{id} — deletes link, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_emergency_contact_email(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-emergency-contact-emails/{id}")
        allure.dynamic.tag("smoke", "emergency-contact-emails")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        contact = _create_emergency_contact(emp_url, authed_session, auth_headers, employee_id, "ecdel")
        email = _create_email_address_for_employee(emp_url, authed_session, auth_headers, employee_id)
        created = _create_resource(
            emp_url, "employees-emergency-contact-emails",
            _contact_email_payload(contact["emergencyContactId"], email["emailAddressId"]),
            authed_session, auth_headers,
        )
        link_id = created["emergencyContactEmailId"]

        with allure.step(f"DELETE /employees-emergency-contact-emails/{link_id}"):
            resp = authed_session.delete(f"{emp_url}/employees-emergency-contact-emails/{link_id}", headers=auth_headers)

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("POST /employees-emergency-contact-emails without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_emergency_contact_email_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees-emergency-contact-emails")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(
            f"{emp_url}/employees-emergency-contact-emails",
            json={"emergencyContactId": 1, "emailAddressId": 1},
        )
        assert resp.status_code in (401, 403, 404)


# ===========================================================================
# EmployeesEmergencyContactPhoneNumbersController
#   — /api/v1/employees-emergency-contact-phone-numbers
# Fields: emergencyContactId, phoneNumberId  →  emergencyContactInfoId
# ===========================================================================

def _contact_phone_payload(contact_id, phone_number_id):
    return {
        "emergencyContactId": contact_id,
        "phoneNumberId": phone_number_id,
    }


def _create_phone_number_for_employee(emp_url, authed_session, auth_headers, employee_id):
    uid = int(_time.time() * 1000) % 10_000_000
    payload = {
        "employeeId": employee_id,
        "phoneNumber": f"555-{str(uid)[:4]}-{str(uid)[4:]}".ljust(12, "0")[:12],
        "type": 1,
        "isPrimary": False,
    }
    return _create_resource(emp_url, "phone-numbers", payload, authed_session, auth_headers)


@allure.suite("User Service – Emergency Contacts")
@allure.feature("Emergency Contact Phone Numbers")
@pytest.mark.employee_emergency_contacts
class TestEmergencyContactPhoneNumbers:

    @allure.title("POST /employees-emergency-contact-phone-numbers — creates link, returns 201")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_emergency_contact_phone(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "POST /employees-emergency-contact-phone-numbers")
        allure.dynamic.tag("smoke", "emergency-contact-phones")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        contact = _create_emergency_contact(emp_url, authed_session, auth_headers, employee_id, "ecph")
        phone = _create_phone_number_for_employee(emp_url, authed_session, auth_headers, employee_id)
        payload = _contact_phone_payload(contact["emergencyContactId"], phone["phoneNumberId"])

        with allure.step("POST /employees-emergency-contact-phone-numbers"):
            resp = authed_session.post(
                f"{emp_url}/employees-emergency-contact-phone-numbers",
                json=payload,
                headers=auth_headers,
            )

        with allure.step("Assert 201 and emergencyContactInfoId"):
            assert resp.status_code == 201
            assert "emergencyContactInfoId" in resp.json()

    @allure.title("GET /employees-emergency-contact-phone-numbers — returns list")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_all_emergency_contact_phones(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contact-phone-numbers")
        allure.dynamic.tag("smoke", "emergency-contact-phones")

        resp = authed_session.get(f"{emp_url}/employees-emergency-contact-phone-numbers", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @allure.title("GET /employees-emergency-contact-phone-numbers/count — returns integer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_count_emergency_contact_phones(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contact-phone-numbers/count")
        allure.dynamic.tag("smoke", "emergency-contact-phones")

        resp = authed_session.get(f"{emp_url}/employees-emergency-contact-phone-numbers/count", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), int)

    @allure.title("GET /employees-emergency-contact-phone-numbers/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_emergency_contact_phone_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contact-phone-numbers/{id}")
        allure.dynamic.tag("negative", "emergency-contact-phones")

        resp = authed_session.get(f"{emp_url}/employees-emergency-contact-phone-numbers/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("GET /employees-emergency-contact-phone-numbers/{id} — returns link for existing id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_emergency_contact_phone_by_id(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "GET /employees-emergency-contact-phone-numbers/{id}")
        allure.dynamic.tag("smoke", "emergency-contact-phones")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        contact = _create_emergency_contact(emp_url, authed_session, auth_headers, employee_id, "ecphid")
        phone = _create_phone_number_for_employee(emp_url, authed_session, auth_headers, employee_id)
        created = _create_resource(
            emp_url, "employees-emergency-contact-phone-numbers",
            _contact_phone_payload(contact["emergencyContactId"], phone["phoneNumberId"]),
            authed_session, auth_headers,
        )
        link_id = created["emergencyContactInfoId"]

        with allure.step(f"GET /employees-emergency-contact-phone-numbers/{link_id}"):
            resp = authed_session.get(f"{emp_url}/employees-emergency-contact-phone-numbers/{link_id}", headers=auth_headers)

        with allure.step("Assert 200 and matching id"):
            assert resp.status_code == 200
            assert resp.json()["emergencyContactInfoId"] == link_id

    @allure.title("DELETE /employees-emergency-contact-phone-numbers/{id} — deletes link, returns 204")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_delete_emergency_contact_phone(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-emergency-contact-phone-numbers/{id}")
        allure.dynamic.tag("smoke", "emergency-contact-phones")

        employee_id = _get_any_employee_id(emp_url, authed_session, auth_headers)
        contact = _create_emergency_contact(emp_url, authed_session, auth_headers, employee_id, "ecphdel")
        phone = _create_phone_number_for_employee(emp_url, authed_session, auth_headers, employee_id)
        created = _create_resource(
            emp_url, "employees-emergency-contact-phone-numbers",
            _contact_phone_payload(contact["emergencyContactId"], phone["phoneNumberId"]),
            authed_session, auth_headers,
        )
        link_id = created["emergencyContactInfoId"]

        with allure.step(f"DELETE /employees-emergency-contact-phone-numbers/{link_id}"):
            resp = authed_session.delete(
                f"{emp_url}/employees-emergency-contact-phone-numbers/{link_id}",
                headers=auth_headers,
            )

        with allure.step("Assert 204"):
            assert resp.status_code == 204

    @allure.title("DELETE /employees-emergency-contact-phone-numbers/{id} — 404 for non-existent id")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_emergency_contact_phone_not_found(self, emp_url, authed_session, auth_headers):
        allure.dynamic.label("endpoint", "DELETE /employees-emergency-contact-phone-numbers/{id}")
        allure.dynamic.tag("negative", "emergency-contact-phones")

        resp = authed_session.delete(f"{emp_url}/employees-emergency-contact-phone-numbers/9999999", headers=auth_headers)
        assert resp.status_code == 404

    @allure.title("POST /employees-emergency-contact-phone-numbers without auth — unauthorized")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_emergency_contact_phone_no_auth(self, emp_url):
        allure.dynamic.label("endpoint", "POST /employees-emergency-contact-phone-numbers")
        allure.dynamic.tag("negative", "auth")

        resp = requests.post(
            f"{emp_url}/employees-emergency-contact-phone-numbers",
            json={"emergencyContactId": 1, "phoneNumberId": 1},
        )
        assert resp.status_code in (401, 403, 404)
