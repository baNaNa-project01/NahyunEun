import os
import requests
import datetime
from flask import Blueprint, redirect, request, jsonify
from flask_jwt_extended import create_access_token
from models import db, User
from flask import Response
import json
from flask_cors import cross_origin
import uuid  

# 🔹 Flask Blueprint 설정
kakao_auth = Blueprint("kakao_auth", __name__)

# ✅ Kakao OAuth 설정
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_URL = "https://kapi.kakao.com/v2/user/me"

FRONT_PAGE_URL= os.getenv("FRONT_PAGE_URL", "http://127.0.0.1:5501/login/kakao/callback")


# ✅ 1️⃣ Kakao 로그인 (JWT 발급)
@kakao_auth.route("/login/kakao")
@cross_origin()
def login_kakao():
    """
    카카오 로그인 시작 엔드포인트
    사용자를 카카오 로그인 페이지로 리다이렉트합니다.
    ---
    tags:
      - Authentication
    responses:
      302:
        description: 카카오 로그인 페이지로 리다이렉트합니다.
    """
    kakao_login_url = (
        f"{KAKAO_AUTH_URL}?client_id={KAKAO_CLIENT_ID}&redirect_uri={KAKAO_REDIRECT_URI}&response_type=code"
    )
    print(f"✅ Redirecting to Kakao: {kakao_login_url}")  # 디버깅용 로그
    return redirect(kakao_login_url)


@kakao_auth.route("/login/kakao/callback")
@cross_origin()
def kakao_callback():
    """
    카카오 로그인 콜백 엔드포인트
    카카오에서 전달받은 authorization code를 사용하여 JWT를 발급하고,
    HttpOnly 쿠키에 토큰을 저장한 후 프론트엔드 페이지로 리다이렉트합니다.
    ---
    tags:
      - Authentication
    parameters:
      - name: code
        in: query
        type: string
        required: true
        description: 카카오에서 전달받은 authorization code
    responses:
      302:
        description: 로그인 성공 후 프론트엔드 페이지로 리다이렉트합니다.
      400:
        description: "카카오 로그인 실패 (예: access_token 미발급)"
    """
    print("요청 파라미터: ", request.args)
    code = request.args.get("code")
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "client_secret": KAKAO_CLIENT_SECRET,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    response = requests.post(KAKAO_TOKEN_URL, data=token_data)
    token_json = response.json()

    if "access_token" not in token_json:
        return "카카오 로그인 실패: " + str(token_json), 400  

    access_token = token_json["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(KAKAO_USER_URL, headers=headers)
    user_info = user_response.json()

    print("🔹 카카오 사용자 정보 응답:", user_info)

    # 🚀 DB에 사용자 저장
    with db.session.begin():
        user = User.query.filter_by(social_id=str(user_info["id"]), provider="kakao").first()
        if not user:
             # ✅ 이메일이 없는 경우 'No Email' 대신 고유한 값으로 변경
            user_email = user_info["kakao_account"].get("email", None)
            if not user_email:
                user_email = f"kakao_{user_info['id']}@kakao.com"  # ✅ 카카오 ID 기반 이메일 생성

            user = User(
                provider="kakao",
                social_id=str(user_info["id"]),
                name=user_info["kakao_account"]["profile"]["nickname"],
                email=user_email
            )
            db.session.add(user)

    # ✅ JWT 발급
    jwt_token = create_access_token(identity=str(user.id), expires_delta=datetime.timedelta(hours=1))

    # ✅ HttpOnly 쿠키 대신, URL 파라미터로 `token` 포함해서 프론트엔드 리다이렉트
    redirect_url = f"{FRONT_PAGE_URL}?token={jwt_token}"
    return redirect(redirect_url)

