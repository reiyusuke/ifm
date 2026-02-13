import os
import time
import uuid

import pytest
import httpx


API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

BUYER_EMAIL = os.getenv("E2E_BUYER_EMAIL", "realbuyer@ifm.com")
BUYER_PASS = os.getenv("E2E_BUYER_PASS", "buyerpass")
SELLER_EMAIL = os.getenv("E2E_SELLER_EMAIL", "seller@ifm.com")
SELLER_PASS = os.getenv("E2E_SELLER_PASS", "sellerpass")


def _wait_health(client: httpx.Client, timeout_sec: float = 5.0) -> None:
    start = time.time()
    while True:
        try:
            r = client.get(f"{API_BASE}/health", timeout=2.0)
            if r.status_code == 200:
                return
        except Exception:
            pass
        if time.time() - start > timeout_sec:
            raise RuntimeError("API health check timed out")
        time.sleep(0.2)


def _login(client: httpx.Client, email: str, password: str) -> str:
    r = client.post(
        f"{API_BASE}/auth/login",
        json={"email": email, "password": password},
        timeout=5.0,
    )
    r.raise_for_status()
    j = r.json()
    token = j.get("access_token")
    assert token, f"login response missing access_token: {j}"
    return token


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_idea_via_sqlite(seller_id: int, title: str, total_score: int, exclusive_price=None) -> int:
    """
    テスト用に sqlite3 CLI で ideas を直接 insert する（DBが sqlite 前提）
    - E2Eのセットアップを最短で済ませるための割り切り
    """
    import subprocess
    import json

    db_path = os.getenv("E2E_DB_PATH", "app.db")

    exclusive_sql = "null" if exclusive_price is None else str(float(exclusive_price))
    sql = f"""
    insert into ideas (seller_id, title, summary, body, price, resale_allowed, exclusive_option_price, status, total_score, created_at)
    values ({int(seller_id)}, {json.dumps(title)}, 'sum', 'body', 100, 0, {exclusive_sql}, 'SUBMITTED', {int(total_score)}, datetime('now'));
    select last_insert_rowid();
    """
    out = subprocess.check_output(["sqlite3", db_path, sql], text=True).strip()
    return int(out)


@pytest.fixture(scope="session")
def client():
    with httpx.Client() as c:
        _wait_health(c)
        yield c


@pytest.fixture(scope="session")
def buyer_token(client: httpx.Client) -> str:
    return _login(client, BUYER_EMAIL, BUYER_PASS)


@pytest.fixture(scope="session")
def seller_token(client: httpx.Client) -> str:
    return _login(client, SELLER_EMAIL, SELLER_PASS)


def test_recommended_filters_owned_and_include_owned(client: httpx.Client, buyer_token: str):
    # include_owned=true は買ってても出る
    r = client.get(f"{API_BASE}/ideas/recommended?include_owned=true", headers=_auth_headers(buyer_token))
    r.raise_for_status()
    assert isinstance(r.json(), list)

    # デフォルトは「未購入のみ」なので、already_owned は必ず False
    r2 = client.get(f"{API_BASE}/ideas/recommended", headers=_auth_headers(buyer_token))
    r2.raise_for_status()
    arr = r2.json()
    assert isinstance(arr, list)
    for x in arr:
        assert x.get("already_owned") is False


def test_recommended_order_by_total_score_desc(client: httpx.Client, buyer_token: str):
    r = client.get(f"{API_BASE}/ideas/recommended?include_owned=true", headers=_auth_headers(buyer_token))
    r.raise_for_status()
    arr = r.json()
    scores = [int(x.get("total_score") or 0) for x in arr]
    assert scores == sorted(scores, reverse=True), f"not sorted desc: {scores}"


def test_buy_hides_from_default_recommended_and_marks_owned_in_include_owned(client: httpx.Client, buyer_token: str):
    """
    DB状態に依存して SKIP しないように、このテスト内で「未購入 idea」を必ず1件作ってから購入する。
    """
    seller_id = int(os.getenv("E2E_SELLER_ID", "3"))
    uniq = uuid.uuid4().hex[:8]
    idea_id = _create_idea_via_sqlite(seller_id, f"e2e-unowned-{uniq}", total_score=42, exclusive_price=None)

    # 作った直後は default recommended に出るはず（未購入）
    r0 = client.get(f"{API_BASE}/ideas/recommended", headers=_auth_headers(buyer_token))
    r0.raise_for_status()
    ids0 = [int(x["id"]) for x in r0.json()]
    assert idea_id in ids0, f"new unowned idea_id={idea_id} not in default recommended: {ids0}"

    # 購入
    buy = client.post(
        f"{API_BASE}/deals",
        headers=_auth_headers(buyer_token),
        json={"idea_id": idea_id, "is_exclusive": False},
    )
    buy.raise_for_status()
    j = buy.json()
    assert j.get("ok") is True

    # default recommended から消える
    r2 = client.get(f"{API_BASE}/ideas/recommended", headers=_auth_headers(buyer_token))
    r2.raise_for_status()
    ids = [int(x["id"]) for x in r2.json()]
    assert idea_id not in ids

    # include_owned=true では already_owned=true で出る
    r3 = client.get(f"{API_BASE}/ideas/recommended?include_owned=true", headers=_auth_headers(buyer_token))
    r3.raise_for_status()
    found = [x for x in r3.json() if int(x["id"]) == idea_id]
    assert found, "purchased idea not found in include_owned=true"
    assert found[0]["already_owned"] is True


def test_exclusive_upgrade_and_no_downgrade(client: httpx.Client, buyer_token: str):
    """
    - exclusive_option_price がある idea を non-exclusive で購入 → is_exclusive=true で upgrade 成功
    - その後 is_exclusive=false で downgrade は 409
    """
    seller_id = int(os.getenv("E2E_SELLER_ID", "3"))
    uniq = uuid.uuid4().hex[:8]
    idea_id = _create_idea_via_sqlite(seller_id, f"e2e-upgrade-{uniq}", total_score=777, exclusive_price=999)

    # まず non-exclusive で購入
    buy = client.post(
        f"{API_BASE}/deals",
        headers=_auth_headers(buyer_token),
        json={"idea_id": idea_id, "is_exclusive": False},
    )
    buy.raise_for_status()
    j1 = buy.json()
    assert j1.get("ok") is True

    # exclusive に upgrade
    up = client.post(
        f"{API_BASE}/deals",
        headers=_auth_headers(buyer_token),
        json={"idea_id": idea_id, "is_exclusive": True},
    )
    up.raise_for_status()
    j2 = up.json()
    assert j2.get("ok") is True
    assert j2.get("upgraded") is True

    # downgrade は 409
    down = client.post(
        f"{API_BASE}/deals",
        headers=_auth_headers(buyer_token),
        json={"idea_id": idea_id, "is_exclusive": False},
    )
    assert down.status_code == 409
    assert down.json().get("detail") == "cannot downgrade exclusive"


def test_exclusive_not_available_returns_400(client: httpx.Client, buyer_token: str):
    """
    exclusive_option_price が null の idea に is_exclusive=true は 400
    """
    # include_owned=true から exclusive_option_price が null の idea を1件探す
    r = client.get(f"{API_BASE}/ideas/recommended?include_owned=true", headers=_auth_headers(buyer_token))
    r.raise_for_status()
    arr = r.json()

    candidate = None
    for x in arr:
        if x.get("exclusive_option_price") is None:
            candidate = x
            break

    if candidate is None:
        pytest.skip("no idea with exclusive_option_price=null found")

    idea_id = int(candidate["id"])

    res = client.post(
        f"{API_BASE}/deals",
        headers=_auth_headers(buyer_token),
        json={"idea_id": idea_id, "is_exclusive": True},
    )
    assert res.status_code == 400
    assert res.json().get("detail") == "exclusive option not available"
