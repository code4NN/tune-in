import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
import datetime

import streamlit as st
import gdown

import pandas as pd
import json


def try_parse_json(x):
    try:
        return json.loads(x) if isinstance(x, str) and x.strip() else None
    except (json.JSONDecodeError, TypeError):
        return None

class SHEET_CONNECTION:
    def __init__(self):
        SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
        ]
        api_key = st.secrets['sheet_api_key']
        sheet_id = st.secrets['sheet_id']['id']
        gc = (gspread
            .authorize(ServiceAccountCredentials
                        .from_json_keyfile_dict(api_key,
                                                SCOPE)
                        )
            )

        self.workbook = gc.open_by_key(sheet_id)
    
    @property
    def now(self):
        india_timezone = pytz.timezone('Asia/Kolkata')
        timestamp = (datetime.datetime.now(india_timezone)
                    .strftime("%Y-%m-%d %H:%M:%S"))
        return timestamp
    
    def get_auth_data(self):
        """
        get all the data from sheet named creds
        """
        array = self.workbook.worksheet('creds').get("A:I")
        
        A1_col = array[0]
        column_header = array[1]
        col_2_A1 = dict(zip(column_header,A1_col))

        auth_data = pd.DataFrame(array[2:],columns=column_header,
                                 )
        json_cols = ['role_list','personal_info','favs','custom_tag_list','custom_kirtan_list']
        for col in json_cols:
            if col in auth_data.columns:
                auth_data[col] = auth_data[col].apply(try_parse_json)

        return {'auth_data':auth_data.copy(),
                'col_2_a1':col_2_A1}
    def auth_get_userdata(self,username,password):
        authdb = self.get_auth_data()
        auth_df = authdb['auth_data'].query(f"username=='{username}'")
        
        if auth_df.shape[0]!=1:
            return 'nouser',{}
        else:
            userdata = list(auth_df.to_dict(orient='index').values())[0]
            if userdata['password'] != password:
                return 'wrong_pass',{}
            else:
                return 'success',userdata
        

    def auth_new_registration(self,payload):

        upload_array_final = [[None,
                              f"""="{payload['username']}" """,
                              f"""="{payload['password']}" """,
                              '="pending"',
                              """["guest"]""",
                              '{}', # personal_info
                              '{}', # favourites
                              '{}', # custom_tag_list
                              '{}' # custom_kirtan_list
                              ]]
        
        (self.workbook.worksheet('creds')
        .append_rows(values=upload_array_final,
                        value_input_option='USER_ENTERED',
                        table_range='A:I'))
        
        # return the new data
        return self.auth_get_userdata(payload['username'],payload['password'])[1]
        
    def auth_update_info(self,A1_range,new_data):
        """
        given range in A1 notation updates the data with new_data
        """
        final_new_data = f'"{new_data}"' if isinstance(new_data,str) else f'"{json.dumps(new_data)}"'
        self.workbook.worksheet('creds').update(A1_range,new_data)
        

