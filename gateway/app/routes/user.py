from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from ..db import (
    get_session,
    self_register_user,
    get_user_by_email,
    verify_user_password,
    list_keys_for_user,
)
from sqlalchemy import text
from ..schemas import SelfRegister, LoginRequest, TokenResponse
from ..user_auth import jwt_encode, jwt_decode, require_user
from ..config import settings

router = APIRouter()


def _html_page(title: str, body: str) -> HTMLResponse:
    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset='utf-8' />
        <meta name='viewport' content='width=device-width, initial-scale=1' />
        <title>{title}</title>
        <style>
          body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 2rem; }}
          form {{ max-width: 420px; margin: 1rem 0; display: grid; gap: .75rem; }}
          input, button {{ padding: .6rem .8rem; font-size: 1rem; }}
          .note {{ color: #666; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border-bottom: 1px solid #eee; text-align: left; padding: .5rem; }}
          .muted {{ color: #999; }}
        </style>
      </head>
      <body>
        <h1>{title}</h1>
        {body}
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/auth/register", response_class=HTMLResponse)
async def register_form():
    body = """
    <form method='post' action='/auth/register'>
      <input name='name' placeholder='Full name' required />
      <input type='email' name='email' placeholder='Email' required />
      <input type='password' name='password' placeholder='Password' required />
      <button type='submit'>Register</button>
    </form>
    <p class='note'>After registering, an admin must approve your account.</p>
    <p class='note'>Already have an account? <a href='/auth/login'>Sign in</a>.</p>
    """
    return _html_page("Create your account", body)


@router.post("/auth/register")
async def register(request: Request):
    # Support both application/json and form submissions
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
        payload = SelfRegister(**data)
    else:
        form = await request.form()
        payload = SelfRegister(name=str(form.get("name")), email=str(form.get("email")), password=str(form.get("password")))

    with get_session() as db:
        existing = get_user_by_email(db, payload.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        rec = self_register_user(db, name=payload.name, email=payload.email, password_plain=payload.password)

    if request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse({"message": "Registered. Await admin approval.", "user": rec})
    # HTML redirect to login page with a note
    body = """
    <p>Registration successful. An admin must approve your account before you can sign in.</p>
    <p><a href='/auth/login'>Go to sign in</a></p>
    """
    return _html_page("Registered", body)


@router.get("/auth/login", response_class=HTMLResponse)
async def login_form():
    body = """
    <form method='post' action='/auth/login'>
      <input type='email' name='email' placeholder='Email' required />
      <input type='password' name='password' placeholder='Password' required />
      <button type='submit'>Sign in</button>
    </form>
    <p class='note'>No account? <a href='/auth/register'>Register</a>.</p>
    """
    return _html_page("Sign in", body)


def _issue_tokens(user: dict) -> TokenResponse:
    base = {"sub": user["id"], "name": user.get("name"), "email": user.get("email"), "role": "user"}
    access = jwt_encode({**base, "typ": "access"}, settings.access_token_ttl_s)
    refresh = jwt_encode({**base, "typ": "refresh"}, settings.refresh_token_ttl_s)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/auth/login")
async def login(request: Request, response: Response):
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
        payload = LoginRequest(**data)
    else:
        form = await request.form()
        payload = LoginRequest(email=str(form.get("email")), password=str(form.get("password")))

    with get_session() as db:
        user = verify_user_password(db, payload.email, payload.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if user.get("status") != "approved":
            raise HTTPException(status_code=403, detail="Account not approved yet")

    tokens = _issue_tokens(user)

    # Set HttpOnly cookies for browser usage
    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie("access_token", tokens.access_token, max_age=settings.access_token_ttl_s, httponly=True, samesite="lax")
    resp.set_cookie("refresh_token", tokens.refresh_token, max_age=settings.refresh_token_ttl_s, httponly=True, samesite="lax")

    # If JSON requested, return tokens instead of redirect
    if request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse(tokens.model_dump())
    return resp


@router.post("/auth/refresh")
async def refresh(request: Request):
    # Prefer Authorization: Bearer <refresh> then fallback to cookie
    auth = request.headers.get("Authorization")
    token = None
    if auth and auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token:
        token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = jwt_decode(token)
    if payload.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Issue new access token
    base = {k: payload.get(k) for k in ("sub", "name", "email")}
    access = jwt_encode({**base, "role": "user", "typ": "access"}, settings.access_token_ttl_s)

    resp = JSONResponse({"access_token": access, "token_type": "bearer"})
    resp.set_cookie("access_token", access, max_age=settings.access_token_ttl_s, httponly=True, samesite="lax")
    return resp


@router.get("/me/keys")
async def my_keys(user: dict = Depends(require_user)):
    with get_session() as db:
        keys = list_keys_for_user(db, user_id=user["sub"])  # list without plaintext
    return {"items": keys}


@router.get("/me/usage")
async def my_usage(user: dict = Depends(require_user)):
    # Aggregate token usage & requests per key for this user (last 30 days)
    params = {"uid": user["sub"]}
    sql = text(
        """
        SELECT key_id, COALESCE(SUM(request_count),0) AS request_count, COALESCE(SUM(total_tokens),0) AS total_tokens
        FROM usage_rollups
        WHERE user_id = :uid AND day >= (CURRENT_DATE - INTERVAL '30 days')
        GROUP BY key_id
        ORDER BY total_tokens DESC
        """
    )
    with get_session() as db:
        rows = db.execute(sql, params).fetchall()
    return {
        "items": [
            {
                "key_id": str(r.key_id) if getattr(r, "key_id", None) else None,
                "request_count": int(r.request_count or 0),
                "total_tokens": int(r.total_tokens or 0),
            }
            for r in rows
        ]
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(require_user)):
    # Load keys and usage
    with get_session() as db:
        keys = list_keys_for_user(db, user_id=user["sub"])  # [{...}]
        rows = db.execute(
            text(
                """
                SELECT key_id, COALESCE(SUM(request_count),0) AS request_count, COALESCE(SUM(total_tokens),0) AS total_tokens
                FROM usage_rollups
                WHERE user_id = :uid AND day >= (CURRENT_DATE - INTERVAL '30 days')
                GROUP BY key_id
                ORDER BY total_tokens DESC
                """
            ),
            {"uid": user["sub"]},
        ).fetchall()

    usage_map = {str(r.key_id): {"request_count": int(r.request_count or 0), "total_tokens": int(r.total_tokens or 0)} for r in rows}

    # Build table
    if not keys:
        tbl = "<p class='muted'>You have no API keys yet. Contact an admin.</p>"
    else:
        rows_html = "".join(
            f"<tr><td>{k['name']}</td><td>{k['last4']}</td><td>{k['status']}</td><td>{usage_map.get(k['id'], {}).get('request_count', 0)}</td><td>{usage_map.get(k['id'], {}).get('total_tokens', 0)}</td></tr>"
            for k in keys
        )
        tbl = f"""
        <table>
          <thead><tr><th>Name</th><th>Last4</th><th>Status</th><th>Requests (30d)</th><th>Tokens (30d)</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
        """

    body = f"""
    <p class='note'>Signed in as <strong>{user.get('email') or user.get('name')}</strong>. <a href='/auth/login'>Switch</a></p>
    <h2>Your API Keys</h2>
    {tbl}
    <h2>Token</h2>
    <form method='post' action='/auth/refresh'>
      <button type='submit'>Refresh Access Token</button>
    </form>
    """
    return _html_page("Dashboard", body)

