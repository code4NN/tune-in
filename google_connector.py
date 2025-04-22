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

        # cached data
        self.colmap = None
        self.authdf = None
        self.kirtan_singer_df = None
    
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

        auth_data = pd.DataFrame(array[2:],columns=column_header)
        json_cols = ['role_list','personal_info','favs','custom_tag_list','custom_kirtan_list']
        for col in json_cols:
            if col in auth_data.columns:
                auth_data[col] = auth_data[col].apply(try_parse_json)
        
        self.colmap = col_2_A1
        self.authdf = auth_data
        return auth_data.copy()
    

    def auth_get_userdata(self,username,password):
        auth_df = self.get_auth_data()
        auth_df = auth_df.query(f"username=='{username}'")
        
        if auth_df.shape[0]!=1:
            return 'nouser',{}
        else:
            userdata = list(auth_df.to_dict(orient='index').values())[0]
            if userdata['password'] != password:
                return 'wrong_pass',{}
            
            elif userdata['full_name']=='pending':
                return 'pending',{}
            
            else:
                return 'success',userdata
        

    def auth_new_registration(self,payload):

        upload_array_final = [None,
                              f"""="{payload['username']}" """, # userame
                              f"""="{payload['password']}" """, # password
                              '="pending"', # full_name
                              """["user"]""", # role_list
                              '{"center":""}', # personal_info
                              '[]', # favourites
                              '[]', # custom_tag_list
                              '[]' # custom_kirtan_list
                              ]
        
        (self.workbook.worksheet('creds')
        .append_row(values=upload_array_final,
                        value_input_option='USER_ENTERED',
                        table_range='A:I'))
        
        # return the new data
        return self.auth_get_userdata(payload['username'],payload['password'])[1]


    def auth_update_info(self,A1_range,new_data):
        """
        given range in A1 notation updates the data with new_data
        """
        final_new_data = f'="{new_data}"' if isinstance(new_data,str) else f'"{json.dumps(new_data)}"'
        self.workbook.worksheet('creds').update(range_name=A1_range,values=[[final_new_data]],raw=False)
    
    def upl_get_singer_list(self,force_refresh=False):
        if (not force_refresh) and (self.kirtan_singer_df is not None):
            pass
        else:
            # download now
            st.toast("refreshing singer list")
            array = self.workbook.worksheet("singer_list").get("A:C")
            column_header = array[0]
            sing_df = pd.DataFrame(array[1:],columns=column_header)
            self.kirtan_singer_df = sing_df
        
        return self.kirtan_singer_df
    
    def upl_enroll_new_singer(self,payload):
        final_payload = [f"""="{payload['hg_hh']}" """,
                         f"""="{payload['full_name']}" """,
                         f"""="{payload['short_name']}" """]
        
        self.workbook.worksheet('singer_list').append_row(values=final_payload,
                                                          value_input_option='USER_ENTERED',
                                                        table_range='A:C')
        
        _ = self.upl_get_singer_list(True)


