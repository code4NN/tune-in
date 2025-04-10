# firebase_init.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

@st.cache_resource
def get_firebase():
    if not firebase_admin._apps:
        my_creds = st.secrets['firebase']

        cred = credentials.Certificate({
            "type": my_creds["type"],
            "project_id": my_creds["project_id"],
            "private_key_id": my_creds["private_key_id"],
            "private_key": my_creds["private_key"],
            "client_email": my_creds["client_email"],
            "client_id": my_creds["client_id"],
            "auth_uri": my_creds["auth_uri"],
            "token_uri": my_creds["token_uri"],
            "auth_provider_x509_cert_url": my_creds["auth_provider_x509_cert_url"],
            "client_x509_cert_url": my_creds["client_x509_cert_url"],
        })
        firebase_admin.initialize_app(cred)
    return firestore.client()