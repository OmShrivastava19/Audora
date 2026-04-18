import os
import time
import requests
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth

def get_firebase_api_key():
    return st.secrets.get("FIREBASE_WEB_API_KEY", "")

def init_firebase_admin():
    if not firebase_admin._apps:
        try:
            # Check if we have standard service account fields in secrets
            if "firebase_admin" in st.secrets:
                creds_dict = dict(st.secrets["firebase_admin"])
                # st.secrets converts inner dicts to AttrDicts, but credentials.Certificate accepts dict
                cred = credentials.Certificate(creds_dict)
                firebase_admin.initialize_app(cred)
            else:
                # Fallback to application default credentials if running in GCP
                firebase_admin.initialize_app()
        except Exception as e:
            st.warning(f"Could not initialize Firebase Admin: {e}")

def get_firestore_client():
    init_firebase_admin()
    return firestore.client()

def sign_up_email_password(email, password):
    api_key = get_firebase_api_key()
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    
    if res.ok:
        data = res.json()
        _sync_user_to_firestore(data["localId"], email)
        return data
        
    error_message = res.json().get("error", {}).get("message", "Sign up failed")
    raise Exception(error_message)

def sign_in_email_password(email, password):
    api_key = get_firebase_api_key()
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    
    if res.ok:
        data = res.json()
        _update_last_login(data["localId"])
        return data
        
    error_message = res.json().get("error", {}).get("message", "Sign in failed")
    raise Exception(error_message)

def _sync_user_to_firestore(uid, email):
    try:
        db = get_firestore_client()
        user_ref = db.collection("users").document(uid)
        doc = user_ref.get()
        if not doc.exists:
            user_ref.set({
                "email": email,
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_login": firestore.SERVER_TIMESTAMP,
                "plan": "free",
                "generations_used": 0
            })
    except Exception as e:
        print(f"Firestore sync error: {e}")

def _update_last_login(uid):
    try:
        db = get_firestore_client()
        user_ref = db.collection("users").document(uid)
        user_ref.update({"last_login": firestore.SERVER_TIMESTAMP})
    except Exception:
        pass

def sign_in_with_google_id_token(google_id_token):
    api_key = get_firebase_api_key()
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}"
    payload = {
        "postBody": f"id_token={google_id_token}&providerId=google.com",
        "requestUri": get_redirect_uri(),
        "returnIdpCredential": True,
        "returnSecureToken": True
    }
    res = requests.post(url, json=payload)
    if res.ok:
        data = res.json()
        _sync_user_to_firestore(data["localId"], data.get("email", ""))
        return data
    error_message = res.json().get("error", {}).get("message", "Google sign in failed")
    raise Exception(error_message)

def get_redirect_uri():
    return st.secrets.get("OAUTH_REDIRECT_URI", "http://localhost:8501")

def get_google_auth_url(redirect_uri):
    client_id = st.secrets.get("OAUTH_CLIENT_ID", "").strip(' "\'')
    if not client_id:
        return None
    url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=openid%20email%20profile"
    return url

def exchange_google_code_for_id_token(code, redirect_uri):
    client_id = st.secrets.get("OAUTH_CLIENT_ID", "").strip(' "\'')
    client_secret = st.secrets.get("OAUTH_CLIENT_SECRET", "").strip(' "\'')
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    res = requests.post(url, data=data)
    if res.ok:
        return res.json().get("id_token")
    raise Exception(f"Failed to exchange auth code with Google. Error: {res.text}")


def init_session_state():
    if "auth" not in st.session_state:
        st.session_state.auth = {
            "is_authenticated": False,
            "uid": None,
            "email": None,
            "id_token": None,
            "refresh_token": None,
            "expires_at": None,
            "plan": "free",
        }

def refresh_token_if_needed(cookies_controller):
    if not st.session_state.auth.get("is_authenticated"):
        return
        
    expires_at = st.session_state.auth.get("expires_at", 0)
    # Refresh if expiring within 5 minutes
    if time.time() > expires_at - 300:
        refresh_token = st.session_state.auth.get("refresh_token")
        if not refresh_token:
            logout_user(cookies_controller)
            return
            
        api_key = get_firebase_api_key()
        url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
        res = requests.post(url, data={"grant_type": "refresh_token", "refresh_token": refresh_token})
        
        if res.ok:
            data = res.json()
            st.session_state.auth["id_token"] = data["id_token"]
            st.session_state.auth["refresh_token"] = data["refresh_token"]
            st.session_state.auth["expires_at"] = time.time() + int(data["expires_in"])
            
            # Update cookie
            cookies_controller.set("refresh_token", data["refresh_token"], max_age=30*24*60*60)
        else:
            logout_user(cookies_controller)

def require_auth_guard(cookies_controller):
    refresh_token_if_needed(cookies_controller)
    if not st.session_state.auth.get("is_authenticated"):
        st.error("Authentication required. Please log in.")
        st.stop()

def logout_user(cookies_controller):
    st.session_state.auth = {
        "is_authenticated": False,
        "uid": None,
        "email": None,
        "id_token": None,
        "refresh_token": None,
        "expires_at": None,
        "plan": "free"
    }
    cookies_controller.remove("refresh_token")
    st.rerun()

def get_user_plan_info(uid):
    try:
        db = get_firestore_client()
        user_ref = db.collection("users").document(uid)
        doc = user_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data.get("plan", "free"), data.get("generations_used", 0)
    except Exception:
        pass
    return "free", 0

def increment_usage(uid):
    try:
        db = get_firestore_client()
        user_ref = db.collection("users").document(uid)
        user_ref.update({"generations_used": firestore.Increment(1)})
        
        usage_ref = db.collection("usage_events").document()
        usage_ref.set({
            "uid": uid,
            "action": "generate_notes",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"Failed to increment usage: {e}")
