import os
import requests
import datetime
from flask import Blueprint, redirect, request, jsonify
from flask_jwt_extended import create_access_token
from models import db, User

google_auth = Blueprint("google_auth", __name__)

# 구글 OAuth 설정
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

@google_auth.route("/login/google")
def login_google():
    google_login_url = (
        f"{GOOGLE_AUTH_URL}?client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code&scope=openid%20email%20profile"
    )
    return redirect(google_login_url)

@google_auth.route("/login/google/callback")
def google_callback():
    code = request.args.get("code")
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(GOOGLE_TOKEN_URL, data=token_data)
    token_json = response.json()
    access_token = token_json.get("access_token")

    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(GOOGLE_USER_INFO_URL, headers=headers)
    user_info = user_response.json()

    with session:
        user = User.query.filter_by(social_id=user_info["id"], provider="google").first()
        if not user:
            user = User(
                provider="google",
                social_id=user_info["id"],
                name=user_info.get("name", "No Name"),
                email=user_info.get("email", "No Email")
            )
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)

    jwt_token = create_access_token(identity=str(user.id), expires_delta=datetime.timedelta(hours=1))
    return jsonify({"message": "구글 로그인 성공", "token": jwt_token})
