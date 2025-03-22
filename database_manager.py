import time


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

