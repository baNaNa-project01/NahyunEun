import os
from flask import Flask, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from models import db, init_db
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

from routes.kakao_auth import kakao_auth
from routes.posts import posts
from routes.google_auth import google_auth


# ✅ 환경 변수 로드
load_dotenv()

# ✅ Flask 앱 설정
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "supersecretkey")

# ✅ Supabase PostgreSQL 데이터베이스 설정
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SUPABASE_DB_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ✅ DB 및 JWT 초기화
db = SQLAlchemy()
jwt = JWTManager(app)

# ✅ 모델 import 후 초기화
from models import db, User, Post, init_db
init_db(app)

# ✅ Flask 컨텍스트에서 DB 생성
with app.app_context():
    print("🚀 데이터베이스 테이블 생성 시작...")
    try:
        db.create_all()
        print("✅ 데이터베이스 테이블 생성 완료!")
    except Exception as e:
        print("❌ 데이터베이스 생성 실패:", str(e))



# ✅ 라우트 등록
app.register_blueprint(kakao_auth)
app.register_blueprint(posts)
app.register_blueprint(google_auth)

# ✅ 사용자 정보 확인 (JWT 필요)
@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    """현재 로그인된 사용자 정보 반환"""
    current_user = get_jwt_identity()
    return jsonify({
        "message": "사용자 정보 조회 성공",
        "user_info": current_user
    })

# ✅ 로그아웃 (JWT 기반이라 별도 로그아웃 불필요)
@app.route("/logout")
@jwt_required()
def logout():
    """클라이언트에서 JWT 삭제하면 로그아웃 완료"""
    return jsonify({"message": "JWT 기반이므로 클라이언트에서 토큰을 삭제하세요."})

# 서버 실행
if __name__ == "__main__":
    app.run(debug=True)
