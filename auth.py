import time
import streamlit as st

def auth_register_me(username,password):
    connection = st.session_state['session'].conn
    try:
        existing_userdf = connection.get_auth_data()
        if username in existing_userdf['username'].tolist():
            return 'username_exists',existing_userdf['username'].tolist()
        else:
            payload= {'username':username,'password':password}
            userdata = connection.auth_new_registration(payload)
            return 'success', userdata
    
    except Exception as e:
        return 'error', e

def auth_validate_userlogin(username,password):
    connection = st.session_state['session'].conn
    try:
        status, response = connection.auth_get_userdata(username,password)
        return status,response
    except Exception as e:
        return 'error', e

        

def auth_update_userinfo():
    pass



def upload_kirtan_now(kirtan_info_dictionary):
    pass

