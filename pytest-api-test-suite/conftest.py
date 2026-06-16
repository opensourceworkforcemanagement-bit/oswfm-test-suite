import time
import pytest
import requests

# ── Hosts ────────────────────────────────────────────────────────────────────
_MICROSERVICE_HOST = "http://localhost:1110"
_MONOLITH_HOST     = "http://localhost:8081"

# ── Microservice URL constants ────────────────────────────────────────────────
_MS_BASE_URL        = f"{_MICROSERVICE_HOST}/api/v1"
_MS_AUTH_BASE_URL   = f"{_MS_BASE_URL}/authentication/users"
_MS_REGISTER_URL    = f"{_MS_AUTH_BASE_URL}/register"
_MS_LOGIN_URL       = f"{_MS_AUTH_BASE_URL}/login"
_MS_USERS_URL       = f"{_MS_BASE_URL}/users"
_MS_BFF_BASE_URL    = f"{_MICROSERVICE_HOST}/api/bff"
_MS_BFF_LOGIN_URL   = f"{_MS_BFF_BASE_URL}/auth/login"
_MS_BFF_ME_URL      = f"{_MS_BFF_BASE_URL}/auth/me"

# ── Monolith URL constants ────────────────────────────────────────────────────
_MONO_BASE_URL      = f"{_MONOLITH_HOST}/api/v1"
_MONO_AUTH_BASE_URL = f"{_MONO_BASE_URL}/authentication/users"
_MONO_REGISTER_URL  = f"{_MONO_AUTH_BASE_URL}/register"
_MONO_LOGIN_URL     = f"{_MONO_AUTH_BASE_URL}/login"
_MONO_USERS_URL     = f"{_MONO_BASE_URL}/users"

# Password rules (from PasswordSecurityProperties defaults):
#   minLength=12, requires upper+lower+digit+special, no 3-char sequences/repeats.
# "Jk#9mWpL@2vN" — 13 chars, all char classes, no sequences, no repeats of 3+.
_PASSWORD = "Jk#9mWpL@2vN"


def pytest_addoption(parser):
    parser.addoption(
        "--monolith",
        action="store_true",
        default=False,
        help="Run tests against the monolith (localhost:8081) instead of the microservice gateway (localhost:1110).",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "auth: authentication flow tests")
    config.addinivalue_line("markers", "user_crud: user CRUD tests")
    config.addinivalue_line("markers", "profile_settings: profile settings tests")
    config.addinivalue_line("markers", "employees: employee CRUD tests")
    config.addinivalue_line("markers", "employee_user: employee-user link tests")
    config.addinivalue_line("markers", "employee_ref_data: employee reference data tests (departments, roles, permissions, org, projects)")
    config.addinivalue_line("markers", "employee_contact_info: employee address / email / phone tests")
    config.addinivalue_line("markers", "employee_emergency_contacts: employee emergency contact tests")
    config.addinivalue_line("markers", "employee_metadata: employee audit log, status history, preferences, settings, SSN tests")


# ── URL fixtures (resolved once per session based on --monolith flag) ─────────

@pytest.fixture(scope="session")
def is_monolith(request):
    return request.config.getoption("--monolith")


@pytest.fixture(scope="session")
def base_url(is_monolith):
    return _MONO_AUTH_BASE_URL if is_monolith else _MS_AUTH_BASE_URL


@pytest.fixture(scope="session")
def users_url(is_monolith):
    return _MONO_USERS_URL if is_monolith else _MS_USERS_URL


@pytest.fixture(scope="session")
def emp_url(is_monolith):
    return _MONO_BASE_URL if is_monolith else _MS_BASE_URL


@pytest.fixture(scope="session")
def login_payload(auth_tokens):
    return {"userName": auth_tokens["userName"], "password": _PASSWORD}


def _setup_session_user(register_url, login_url, bff_login_url, bff_me_url):
    """Register a fresh user, login, and return tokens + an authenticated session.

    Microservice mode:
      - Register + raw-token login go through the auth service.
      - BFF login (POST /api/bff/auth/login) establishes the APPSESSION cookie
        the gateway's JwtAuthenticationFilter requires for session-protected routes.

    Monolith mode (bff_login_url=None):
      - No BFF layer; register + direct login only.

    Retries once on 500 to work around a service-side race in PasswordService.
    """
    for attempt in range(2):
        uid = f"apitestuser{int(time.time() * 1000) % 1_000_000_000}"
        payload = {
            "email": f"{uid}@chere.com",
            "userName": uid,
            "password": _PASSWORD,
            "firstName": "Api",
            "middleName": "",
            "lastName": "Tester",
        }

        reg = requests.post(register_url, json=payload)
        if reg.status_code != 200:
            if attempt == 0:
                time.sleep(0.5)
                continue
            pytest.fail(f"Setup register failed: {reg.status_code} {reg.text}")

        session = requests.Session()

        if bff_login_url:
            # Microservice only: BFF login establishes the APPSESSION cookie.
            bff_resp = session.post(
                bff_login_url,
                json={"userName": uid, "password": _PASSWORD},
            )
            if bff_resp.status_code != 200:
                if attempt == 0:
                    time.sleep(1)
                    continue
                pytest.fail(f"BFF login failed: {bff_resp.status_code} {bff_resp.text}")

            # Issue a GET so csrfCookieWebFilter writes the XSRF-TOKEN cookie.
            session.get(bff_me_url)

        # Raw-token login — use same session so only one login exists.
        login_resp = session.post(
            login_url,
            json={"userName": uid, "password": _PASSWORD},
        )
        if login_resp.status_code != 200:
            pytest.fail(f"Auth login failed: {login_resp.status_code} {login_resp.text}")

        body = login_resp.json()
        xsrf_token = session.cookies.get("XSRF-TOKEN", "")
        print(f"\n[conftest] login cookies: {dict(session.cookies)}")
        return {
            "accessToken":  body["response"]["accessToken"],
            "refreshToken": body["response"]["refreshToken"],
            "userName":     uid,
            "session":      session,
            "xsrfToken":    xsrf_token,
        }
    pytest.fail("Setup failed after retries")


@pytest.fixture(scope="session")
def auth_tokens(is_monolith):
    if is_monolith:
        return _setup_session_user(
            register_url=_MONO_REGISTER_URL,
            login_url=_MONO_LOGIN_URL,
            bff_login_url=None,
            bff_me_url=None,
        )
    return _setup_session_user(
        register_url=_MS_REGISTER_URL,
        login_url=_MS_LOGIN_URL,
        bff_login_url=_MS_BFF_LOGIN_URL,
        bff_me_url=_MS_BFF_ME_URL,
    )


@pytest.fixture(scope="session")
def access_token(auth_tokens):
    return auth_tokens["accessToken"]


@pytest.fixture(scope="session")
def refresh_token(auth_tokens):
    return auth_tokens["refreshToken"]


@pytest.fixture(scope="session")
def authed_session(auth_tokens):
    """requests.Session carrying the gateway SESSION cookie from login.
    The running JwtAuthenticationFilter checks ACCESS_TOKEN in that server-side
    session, so any session-protected endpoint needs this session object."""
    return auth_tokens["session"]


@pytest.fixture(scope="session")
def xsrf_token(auth_tokens):
    return auth_tokens["xsrfToken"]


@pytest.fixture(scope="session")
def auth_headers(access_token, xsrf_token):
    """Headers for state-changing requests through the BFF gateway.

    The gateway uses the Token Vault pattern: the JWT lives server-side in the
    APPSESSION; the browser/client never sends it.  The Authorization header here
    is only used by endpoints that accept raw-token auth (e.g. the auth-service
    proxied routes).  State-changing requests to /api/v1/** also require the
    X-XSRF-TOKEN header to pass the gateway's CSRF filter.
    """
    return {
        "Authorization": f"Bearer {access_token}",
        "X-XSRF-TOKEN":  xsrf_token,
    }
