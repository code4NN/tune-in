import time

from firebase_connector import get_firebase

DB = get_firebase()
from hashlib import sha256

def hash_password(password):
    """ Hash the password using SHA-256 """
    return sha256(password.encode()).hexdigest()

def register_user(username, password):
    """
    Register a user in Firestore.
    - If the username is already taken, returns a list of existing usernames.
    - If registration is successful, returns the user document data.
    """
    # Check if the username already exists
    try:
        existing_users_ref = DB.collection('users').where('username', '==', username).stream()
        existing_usernames = [user.id for user in existing_users_ref]
        
        if existing_usernames:
            # If username is taken, return the list of existing usernames
            return False,existing_usernames,'username'
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Create a new user document
        if username=='admin' and password=='admin':
            user_data = {
                'username': username,
                'password': hashed_password,
                'is_verified': True,  # Default: unverified
                'access_level': ['user','admin'],  # Default: basic user
                'favorites': []  # Empty list of favorites for the user
            }
        else:
            user_data = {
                'username': username,
                'password': hashed_password,
                'is_verified': False,  # Default: unverified
                'access_level': ['user'],  # Default: basic user
                'favorites': []  # Empty list of favorites for the user
            }
        
        # Add the user to Firestore
        DB.collection('users').document(username).set(user_data)
        
        # Return the user document data
        user_doc = db.collection('users').document(username).get()
        return True,user_doc.to_dict(),None
    
    except Exception as e:
        return False, e, None


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

