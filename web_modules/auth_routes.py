# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

from flask import redirect, render_template_string, request, session, url_for

from web_modules.templates import LOGIN_PAGE_TEMPLATE, REGISTER_PAGE_TEMPLATE


def register_auth_routes(app, deps: dict) -> None:
    load_users = deps["load_users"]
    save_users = deps["save_users"]
    verify_password = deps["verify_password"]
    hash_password = deps["hash_password"]
    is_valid_username = deps["is_valid_username"]
    login_blocked_until = deps["login_blocked_until"]
    record_login_failure = deps["record_login_failure"]
    clear_login_failures = deps["clear_login_failures"]
    ensure_user_space = deps["ensure_user_space"]
    reload_user_jobs = deps["reload_user_jobs"]

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        note = None
        if request.method == "POST":
            username = (request.form.get("username", "") or "").strip()
            password = (request.form.get("password", "") or "").strip()
            if not username or not password:
                error = "请输入用户名和密码。"
            elif (blocked_until := login_blocked_until(username)):
                wait_seconds = max(1, int((blocked_until - datetime.now()).total_seconds()))
                error = f"登录失败次数过多，请 {wait_seconds} 秒后再试。"
            else:
                users = load_users()
                user = users.get(username)
                if not user:
                    record_login_failure(username)
                    error = "用户名或密码错误。"
                elif not verify_password(user, password):
                    record_login_failure(username)
                    error = "用户名或密码错误。"
                else:
                    if ":" not in str(user.get("password_hash", "")):
                        user["password_hash"] = hash_password(password)
                        user.pop("salt", None)
                        users[username] = user
                        save_users(users)
                    session["username"] = username
                    clear_login_failures(username)
                    ensure_user_space(username)
                    reload_user_jobs(username)
                    return redirect(url_for("index"))
        return render_template_string(LOGIN_PAGE_TEMPLATE, error=error, note=note)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        error = None
        note = None
        if request.method == "POST":
            username = (request.form.get("username", "") or "").strip()
            password = (request.form.get("password", "") or "").strip()
            password2 = (request.form.get("password2", "") or "").strip()
            if not username or not password:
                error = "请输入用户名和密码。"
            elif len(password) < 6:
                error = "密码至少需要 6 个字符。"
            elif password != password2:
                error = "两次输入的密码不一致。"
            elif len(username) < 3 or len(username) > 20:
                error = "用户名长度必须为 3-20 个字符。"
            elif not is_valid_username(username):
                error = "用户名只能包含字母、数字、下划线或连字符。"
            else:
                users = load_users()
                if username in users:
                    error = "用户名已被注册。"
                else:
                    users[username] = {"password_hash": hash_password(password)}
                    save_users(users)
                    ensure_user_space(username)
                    note = "注册成功，请登录。"
        return render_template_string(REGISTER_PAGE_TEMPLATE, error=error, note=note)

    @app.route("/logout", methods=["POST"])
    def logout():
        session.pop("username", None)
        session.pop("csrf_token", None)
        return redirect(url_for("index"))
