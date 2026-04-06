import requests
import json

BASE_URL = "http://localhost:8000"

# 1. 登录获取 token
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "六六", "password": "123456q"}
)

if login_response.status_code != 200:
    print(f"❌ 登录失败: {login_response.text}")
    exit(1)

tokens = login_response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

print(f"✅ 登录成功")
print(f"Access Token: {access_token[:50]}...")
print(f"Refresh Token: {refresh_token[:50]}...")

# ── 新增代码：获取当前用户信息 ───────────────────────────────
print("\n--- 测试获取当前用户信息 ---")
me_response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}  # 关键：带上 access_token
)

if me_response.status_code == 200:
    user_info = me_response.json()
    print(f"✅ 获取用户信息成功:")
    print(f"   - 用户ID: {user_info.get('id')}")
    print(f"   - 用户名: {user_info.get('username')}")
    print(f"   - 角色: {user_info.get('role')}")
else:
    print(f"❌ 获取用户信息失败: {me_response.status_code}")
    print(f"   - 错误信息: {me_response.text}")

# 2. 调用登出接口
logout_response = requests.post(
    f"{BASE_URL}/auth/logout",
    headers={"Authorization": f"Bearer {access_token}"},
    json={"refresh_token": refresh_token}
)

print(f"\n登出状态码: {logout_response.status_code}")
print(f"登出响应: {logout_response.json()}")

# 3. 验证登出是否成功（再次用 refresh_token 刷新应该失败）
if logout_response.status_code == 200:
    print("\n✅ 登出成功，验证 refresh_token 已被撤销...")

    refresh_response = requests.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    print(f"刷新状态码: {refresh_response.status_code}")
    if refresh_response.status_code == 401:
        print("✅ 确认：refresh_token 已被撤销，无法再次使用")
    else:
        print(f"⚠️ 警告：refresh_token 仍然有效 - {refresh_response.text}")