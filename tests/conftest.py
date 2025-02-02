#!/usr/bin/env python3
"""Yoda tests configuration."""

__copyright__ = 'Copyright (c) 2020-2022, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import json
import re

import pytest
import requests
import urllib3
from pytest_bdd import (
    given,
    parsers,
    then,
    when,
)


portal_url = ""
api_url = ""
roles = {}
user_cookies = {}

datarequest = False
deposit = False
intake = False
run_all = False


def pytest_addoption(parser):
    parser.addoption("--datarequest", action="store_true", default=False, help="Run datarequest tests")
    parser.addoption("--deposit", action="store_true", default=False, help="Run deposit tests")
    parser.addoption("--intake", action="store_true", default=False, help="Run intake tests")
    parser.addoption("--all", action="store_true", default=False, help="Run all tests")
    parser.addoption("--environment", action="store", default="environments/development.json", help="Specify configuration file")


def pytest_configure(config):
    config.addinivalue_line("markers", "datarequest: Run datarequest tests")
    config.addinivalue_line("markers", "deposit: Run deposit tests")
    config.addinivalue_line("markers", "intake: Run intake tests")
    config.addinivalue_line("markers", "all: Run all tests")

    global environment
    environment = config.getoption("--environment")

    with open(environment) as f:
        configuration = json.loads(f.read())

    global portal_url
    portal_url = configuration.get("url", "https://portal.yoda.test")

    global api_url
    api_url = "{}/api".format(portal_url)

    global roles
    roles = configuration.get("roles", {})

    # Store cookies for each user.
    for role, user in roles.items():
        csrf, session = login(user["username"], user["password"])
        user_cookies[role] = (csrf, session)

    global datarequest, deposit, intake, run_all
    datarequest = config.getoption("--datarequest")
    deposit = config.getoption("--deposit")
    intake = config.getoption("--intake")
    run_all = config.getoption("--all")
    if run_all:
        datarequest = True
        deposit = True
        intake = True


def pytest_bdd_apply_tag(tag, function):
    if tag == 'datarequest' and not datarequest:
        marker = pytest.mark.skip(reason="Skip datarequest")
        marker(function)
        return True
    elif tag == 'deposit' and not deposit:
        marker = pytest.mark.skip(reason="Skip deposit")
        marker(function)
        return True
    elif tag == 'intake' and not intake:
        marker = pytest.mark.skip(reason="Skip intake")
        marker(function)
        return True
    elif tag == "fail":
        marker = pytest.mark.xfail(reason="Test is expected to fail", run=True, strict=False)
        marker(function)
        return True
    else:
        # Fall back to pytest-bdd's default behavior
        return None


def pytest_bdd_after_scenario(request, feature, scenario):
    """Logout user after scenario when we have a browser."""
    if feature.rel_filename.startswith("ui/"):
        try:
            browser = request.getfixturevalue('browser')
            url = "{}/user/logout".format(portal_url)
            browser.visit(url)
        except pytest.FixtureLookupError:
            # No UI logout for API tests.
            pass
        except urllib3.exceptions.MaxRetryError:
            # Prevent spamming log after keyboard interrupt.
            pass


def login(user, password):
    """Login portal and retrieve CSRF and session cookies."""
    # Disable unsecure connection warning.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    url = "{}/user/login".format(portal_url)

    client = requests.session()

    # Retrieve the login CSRF token.
    content = client.get(url, verify=False).content.decode()
    p = re.compile("tokenValue: '([a-zA-Z0-9._-]*)'")
    csrf = p.findall(content)[0]

    # Login as user.
    login_data = dict(csrf_token=csrf, username=user, password=password, next='/')
    response = client.post(url, data=login_data, headers=dict(Referer=url), verify=False)
    session = client.cookies['__Host-session']
    client.close()

    # Retrieve the authenticated CSRF token.
    content = response.content.decode()
    p = re.compile("tokenValue: '([a-zA-Z0-9._-]*)'")
    csrf = p.findall(content)[0]

    # Return CSRF and session cookies.
    return csrf, session


def api_request(user, request, data, timeout=10):
    # Retrieve user cookies.
    csrf, session = user_cookies[user]

    # Disable unsecure connection warning.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Make API request.
    url = api_url + "/" + request
    files = {'csrf_token': (None, csrf), 'data': (None, json.dumps(data))}
    cookies = {'__Host-session': session}
    headers = {'referer': portal_url}
    response = requests.post(url, headers=headers, files=files, cookies=cookies, verify=False, timeout=timeout)

    # Remove debug info from response body.
    body = response.json()
    if "debug_info" in body:
        del body["debug_info"]

    return (response.status_code, body)


def upload_data(user, file, folder, file_content="test"):
    # Retrieve user cookies.
    csrf, session = user_cookies[user]

    # Disable unsecure connection warning.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Make POST request.
    url = portal_url + "/research/upload"

    files = {"csrf_token": (None, csrf),
             "filepath": (None, folder),
             "flowChunkNumber": (None, "1"),
             "flowChunkSize": (None, "10485760"),
             "flowCurrentChunkSize": (None, "4"),
             "flowTotalSize": (None, "4"),
             "flowIdentifier": (None, "4-{}".format(file)),
             "flowFilename": (None, file),
             "flowRelativePath": (None, file),
             "flowTotalChunks": (None, "1"),
             "file": (file, file_content)}

    cookies = {'__Host-session': session}
    headers = {'referer': portal_url}
    response = requests.post(url, headers=headers, files=files, cookies=cookies, verify=False, timeout=10)

    return (response.status_code, response)


def post_form_data(user, request, files):
    # Retrieve user cookies.
    csrf, session = user_cookies[user]

    # Disable unsecure connection warning.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Make POST request.
    url = portal_url + "/" + request
    files['csrf_token'] = (None, csrf)
    cookies = {'__Host-session': session}
    headers = {'referer': portal_url}
    response = requests.post(url, headers=headers, files=files, cookies=cookies, verify=False, timeout=10)

    return (response.status_code, response)


@given(parsers.parse("user {user:w} is authenticated"), target_fixture="user")
def api_user_authenticated(user):
    assert user in roles
    return user


@given(parsers.parse('user {user} is logged in'), target_fixture="user")
@when(parsers.parse('user {user} logs in'))
def ui_login(browser, user):
    url = "{}/user/gate".format(portal_url)
    browser.visit(url)

    # Fill in username
    try:
        browser.find_by_id('f-login-username').fill(roles[user]["username"])
    except KeyError:
        browser.find_by_id('f-login-username').fill(user)
    browser.find_by_id('f-login-submit').click()

    # Fill in password
    try:
        browser.find_by_id('f-login-password').fill(roles[user]["password"])
    except KeyError:
        browser.find_by_id('f-login-password').fill("test")

    # Find and click the 'Sign in' button
    browser.find_by_id('f-login-submit').click()


@given('user is not logged in')
def ui_logout(browser):
    url = "{}/user/logout".format(portal_url)
    browser.visit(url)


@when(parsers.parse("user {user} enters email address"))
def ui_gate_username(browser, user):
    # Fill in username
    try:
        browser.find_by_id('f-login-username').fill(roles[user]["username"])
    except KeyError:
        browser.find_by_id('f-login-username').fill(user)

    # Find and click the 'Next' button
    browser.find_by_id('f-login-submit').click()


@given('the user is redirected to the login page')
@then('the user is redirected to the login page')
def ui_login_assert_login_page(browser):
    assert (
        "{}/user/login".format(portal_url) in browser.url
        or "{}/user/gate".format(portal_url) in browser.url)


@given(parsers.parse('module "{module}" is shown'))
@when(parsers.parse('module "{module}" is shown'))
@then(parsers.parse('module "{module}" is shown'))
@given(parsers.parse('page "{module}" is shown'))
@when(parsers.parse('page "{module}" is shown'))
def ui_module_shown(browser, module):
    if "/" in module:
        url = "{}/{}".format(portal_url, module)
    else:
        url = "{}/{}/".format(portal_url, module)
    browser.visit(url)


@given(parsers.parse('text "{text}" is shown'))
@when(parsers.parse('text "{text}" is shown'))
@then(parsers.parse('text "{text}" is shown'))
def ui_text_shown(browser, text):
    assert browser.is_text_present(text)


@then(parsers.parse('the response status code is "{code:d}"'))
def api_response_code(api_response, code):
    http_status, _ = api_response
    assert http_status == code


@given(parsers.parse("collection {collection} exists"))
def collection_exists(user, collection):
    http_status, _ = api_request(
        user,
        "browse_folder",
        {"coll": collection}
    )
    assert http_status == 200


@given(parsers.parse("{collection} is unlocked"))
def collection_is_unlocked(user, collection):
    _, body = api_request(
        user,
        "research_collection_details",
        {"path": collection}
    )

    if body["data"]["status"] == "LOCKED":
        http_status, _ = api_request(
            user,
            "folder_unlock",
            {"coll": collection}
        )
        assert http_status == 200
    else:
        assert body["data"]["status"] == "" or body["data"]["status"] == "SECURED"


@given(parsers.parse("{collection} is locked"))
def collection_is_locked(user, collection):
    _, body = api_request(
        user,
        "research_collection_details",
        {"path": collection}
    )

    if body["data"]["status"] != "LOCKED":
        http_status, _ = api_request(
            user,
            "folder_lock",
            {"coll": collection}
        )
        assert http_status == 200
    else:
        assert body["data"]["status"] == "LOCKED"


@given(parsers.parse("the user navigates to {page}"))
@when(parsers.parse("the user navigates to {page}"))
def ui_login_visit_groupmngr(browser, page):
    browser.visit("{}{}".format(portal_url, page))


@then(parsers.parse("the user is redirected to {page}"))
def ui_user_redirected(browser, page):
    target = "{}{}".format(portal_url, page)

    assert browser.url == target


@when(parsers.parse("user browses to folder {folder}"))
@then(parsers.parse("user browses to folder {folder}"))
def ui_browse_folder(browser, folder):
    link = []
    while len(link) == 0:
        link = browser.links.find_by_partial_text(folder)
        if len(link) > 0:
            link.click()
        else:
            browser.find_by_id('file-browser_next').click()
