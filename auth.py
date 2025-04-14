import time
import streamlit as st

def auth_register_me(username,password):
    connection = st.session_state['session'].conn
    try:
        existing_userdf = connection.get_auth_data()['auth_data']
        if username in existing_userdf['username'].tolist():
            return False,{'problem':'username','existing_userlist':existing_userdf['username'].tolist()}
        else:
            payload= {'username':username,'password':password}
            userdata = connection.auth_new_registration(payload)
            return True, {'data':userdata}
    
    except Exception as e:
        return False, {'problem':'','error':e}

def auth_validate_userlogin(username,password):
    connection = st.session_state['session'].conn
    try:
        status, response = connection.auth_get_userdata(username,password)
        if status=='nouser':
            return False,{'problem':'username'}
        elif status=='wrong_pass':
            return False,{"problem":'password'}
        else:
            return True,{'data':response}
    except Exception as e:
        return False, {'problem':'','error':e}

        

def auth_update_userinfo():
    pass

def validate_user_login(username,password):
    time.sleep(3)
    userdata = {
        'shivendra': {
            'password': 'password'}
    }
    if username not in userdata:
        return False, {'error': 'User not found'}
    elif userdata[username]['password'] != password:
        return False, {'error': 'Invalid Password'}
    else:
        # all set
        return True, {'data': {'username': username}}

def upload_kirtan_now(kirtan_info_dictionary):
    pass

