import streamlit as st
import pandas as pd
import time

from google_connector import SHEET_CONNECTION
# for authorization related functions
from auth import auth_register_me
from auth import auth_validate_userlogin
from auth import auth_update_userinfo

# for kirtan related functions
from k_uploader import get_kirtan_info

class SessionManager:
    def __init__(self):

        try:
            self.conn = SHEET_CONNECTION()
        except Exception as e:
            st.error(e)
            st.stop()
        
        self.login = {
            'is_logged_in': False,
            'start_validation':False,
            'start_registering':False,
            'existing_username':[],
            'user_creds': None,
        }

        self.navigate = {
            'active_page':'kirtans'
        }
        
        self.upload_kirtan = {
            'kf_available':False,
            'kirtan_info': None,
            'clipped_audio':None,
            'process_step_1':False,
            'bookmark_list': [{'start_time':0,'start_time_raw':0,'display_time':'0m 0s','tune_hint':''}],
            'process_step_2':False
        }

        self.ux = {}
if 'session' not in st.session_state:
    st.session_state.session = SessionManager()
session = st.session_state['session']

# ===============================================================================
# ----------- Login Page ------------
def login_page():
    st.markdown("## :gray[log]:rainbow[in] :gray[2] :gray[tune]:rainbow[in]")
    st.markdown(
    """
    <style>
    #login-2-tunein {
        text-align: center;
        display: block;
    }
    .stButton {
        text-align: center;
        display: block;
    }
    </style>
    """,
    unsafe_allow_html=True
    )

    cols = st.columns([1,3,1])
    contains_space = lambda x: len(x) !=len(x.replace(" ",''))
    valid_creds = True
    with cols[1]:
        username = st.text_input(":gray[username]")
        if username and contains_space(username):
            st.caption(":red[username cannot have space]")
            valid_creds = False

        st.markdown("")
        password = st.text_input(":gray[Password]", type="password")
        if password and contains_space(password):
            st.caption(":red[password cannot have space]")
            valid_creds = False

        st.markdown("")
        st.markdown("")
    
        error_msg = st.empty()
        login_button = st.empty()
        is_registering_place = st.empty()
        is_registering = is_registering_place.checkbox(":gray[I don't have an account]")

        if is_registering:
            if len(username)<4:
                error_msg.error("Username should be at least 4 character long")
            elif username in session.login['existing_username']:
                error_msg.error("username have been taken by someone")

            elif len(password) <4:
                error_msg.error("password should be at least 4 character long")
            else:
                login_button.button("Register Now",type='primary',
                on_click=lambda : session.login.update({"start_registering":True}),
                key='register_button'
                )

        elif username and password:
            is_registering_place.empty()
            login_button.button("Login",
            on_click=lambda : session.login.update({'start_validation':True}),
                                key='login-button')
        else:
            login_button.button("Login",disabled=True)
        
        # =========================================================== action ground
        if session.login['start_validation']:
            session.login.update({'start_validation':False})

            with st.spinner("Validating Credentials..."):
                login_button.empty()
                status,response = auth_validate_userlogin(username,password)
            
            if status=='success':
                session.login.update({'is_logged_in':True,'user_creds':response})
                error_msg.success("Login Successful!")
                with st.spinner("going to main page..."):
                    time.sleep(2)
                st.rerun()
            elif status=='nouser':
                error_msg.error("Username does not exist")
            elif status=='wrong_pass':
                error_msg.error("incorrect password")
            elif status=='pending':
                error_msg.warning("your registration is in progress")
            else:
                st.error(response)


        elif session.login['start_registering']:
            session.login.update({'start_registering':False})

            with st.spinner("Onboarding..."):
                login_button.empty()
                status,response = auth_register_me(username,password)
            
            if status=='success':
                error_msg.success("you have registered")

            elif status=='username_exists':
                error_msg.error("username already exists")
                session.login.update({'existing_username':response})
            else :
                st.error(response)

def approve_regs():
    st.subheader(":green[Approve Pending Registrations]")
    st.button("Refresh now",on_click=lambda: session.conn.get_auth_data())
    pending_df = session.conn.authdf.query("full_name=='pending'").copy()
    
    if pending_df.shape[0]<1:
        st.success("No More Pending Registrations")
    else:
        pending_df.insert(0,'select',False)

        editeddf = st.data_editor(pending_df,
                                column_config={'select':st.column_config.CheckboxColumn(label="Pick",width='small',disabled=False),
                                               'username':st.column_config.TextColumn(label="User",width='medium',disabled=True)},
                                               column_order=['select','username'],
                                               hide_index=True)
        editeddf = editeddf.query("select==True")
        # editeddf
        if editeddf.shape[0]!=1:
            st.warning("Please select only one user at a time")
        else:
            active_user = list(editeddf.to_dict(orient='index').values())[0]
            st.write(active_user)
            full_name = st.text_input("Enter full name",key='new_name')
            
            if full_name:
                def approve_now():
                    column_letter = session.conn.colmap['full_name']
                    row_number = active_user['row_num']
                    upload_range = f"{column_letter}{row_number}"
                    session.conn.auth_update_info(upload_range,full_name)
                    session.conn.get_auth_data()

                st.button("Approve now",
                          on_click=approve_now)

# ----------- Upload Kirtan ------------
def upload_kirtan():
    st.subheader(":rainbow[Upload a Kirtan]")
    with st.expander("Steps to upload a Kirtan module",expanded=True):
        st.markdown("""
        1. **Upload an audio file** (MP3 or M4A) (or enter drive link)
        2. **Choose start and end time** to locate the Kirtan
        3. Click **"Clip Kirtan"** to trim the audio (duration between 1 min and 30 min)
        4. Add **singer** and other details
        5. Add **multiple timestamps** to bookmark starting point of Mahamantra (e.g., Tune-1, Tune-2).  
        6. Hit **"Upload and Share"** to complete
        """)
    st.divider()

    uploaded_file = st.file_uploader("Upload MP3", type=["mp3"])
    
    # if True:
    if uploaded_file:
        # ================================================================ stage-1 get info
        if not session.upload_kirtan['kf_available']:
            st.divider()
            st.subheader(":gray[Step 1: ] :blue[Locate Kirtan]")
            # st.audio(uploaded_file, format="audio/mp3")
            
            is_success,response = get_kirtan_info(uploaded_file)
            
            if is_success :
                st.divider()
                cols = st.columns(3)
                cols[1].button("Proceed to next step",
                          on_click=lambda : session.upload_kirtan.update({'process_step_1':True}),
                          type='primary')
                # process the step one and jump to next step
                # if session.upload_kirtan['process_step_1']:
                #     with st.spinner("clipping the audio..."):
                #         # response['clip_file'] = trim_audio(uploaded_file,
                #                                             response['start_time'],
                #                                             response['duration'])
                #         session.upload_kirtan.update({'kf_available':True,
                #                                       'kirtan_info':response})
                        
                #         session.upload_kirtan.update({'process_step_1':False})
                #         st.rerun()
        
        else:
            # ========================================================= show stage 1 info
            st.subheader(":green[Step 1: Add Bookmarks]")
            kirtan_info = session.upload_kirtan['kirtan_info']
            step_1_value = pd.DataFrame([
                        ['start_time',kirtan_info['start_time']],
                      ['end_time',kirtan_info['end_time']],
                      ['duration',kirtan_info['duration']],
                      ['singer',kirtan_info['singer']],
                      ['tune_name',kirtan_info['tune_name']]],columns=['field','value'])
            step_1_value['field'] = step_1_value['field'].str.replace("_"," ").str.title()
            st.dataframe(step_1_value,hide_index=True)
            cols = st.columns(3)
            cols[1].button('Edit Step 1',on_click=lambda : session.upload_kirtan.update({'kf_available':False,
                                                                                     'kirtan_info':None}))
            st.subheader(":gray[Step 2: ] :blue[Add Bookmarks]")
            # ======================================================= stage 2 get bookmarks
            # st.audio(kirtan_info['clip_file'], format="audio/mp3")
            st.caption("Now add bookmarks with tune-1, tune-2 etc. and add a hint to remember")
            
            error_list = []
            # with st.expander("before"):
            #     st.write(session.upload_kirtan['bookmark_list'])
            
            def update_bookmark(index,field,value_identifier):
                if field=='start_time':
                    entered_time = st.session_state[value_identifier]
                    is_success, timedata = is_valid_timestamp(entered_time,True)
                    if is_success:
                        session.upload_kirtan['bookmark_list'][index].update({'start_time':timedata['duration'],
                                                                              'start_time_raw':entered_time,
                                                                            'display_time':timedata['display_text']})
                else:
                    session.upload_kirtan['bookmark_list'][index].update({field:st.session_state[value_identifier].strip()})
            
            bookmark_list = session.upload_kirtan['bookmark_list']
            for index,bookmark in enumerate(bookmark_list,start=0):
                st.markdown(f"#### :gray[Tune {index+1}] :blue[{bookmark.get('display_time','')}]")
                cols = st.columns([2,2,1])
                bm_error = False
                
                with cols[0]:
                    if 'start_time' in bookmark.keys():
                        start_time_raw = st.number_input(":gray[start time]",
                                                                        min_value=0 if index==0 else bookmark_list[index-1]['start_time_raw'],
                                                                        value=bookmark['start_time_raw'],
                                                                        key=f"number_inp_{index}",
                                                                        on_change=update_bookmark,
                                                                        args=[index,'start_time',f"number_inp_{index}"]
                                                                        )
                    else:
                        start_time_raw = st.number_input(":blue[start time]",
                                                                        min_value=0 if index==0 else bookmark_list[index-1]['start_time_raw'],
                                                                        key=f"number_inp_{index}",
                                                                        on_change=update_bookmark,
                                                                        args=[index,'start_time',f"number_inp_{index}"]
                                                                        )
                    start_time_response = is_valid_timestamp(start_time_raw)
                    bm_error = not start_time_response[0]
                    
                with cols[1]:
                    tune_hint = st.text_input(":gray[Tune Hint]",
                                                                   value=bookmark['tune_hint'],
                                                                   key=f"tune_hint_inp_{index}",
                                                                   on_change=update_bookmark,
                                                                    args=[index,'start_time',f"number_inp_{index}"]
                                                                   
                                                                   ).strip()
                    if tune_hint == '':
                        bm_error = True
                        st.caption(":red[hint please]")
                
                error_list.append(bm_error)
                with cols[2]:
                    if not  bm_error:
                        
                        def process_action(actiontype,index):
                            if actiontype == 'del':
                                session.upload_kirtan['bookmark_list'].pop(index)
                            elif actiontype == 'add':
                                session.upload_kirtan['bookmark_list'].append({'tune_hint':''})
                        
                        st.button(f'➕',
                                    on_click=process_action,
                                    args=['add',index],key=f"add_btn_{index}")
                        if index > 0:
                            st.button(f'❌',
                                        on_click=process_action,
                                        args=['del',index],key=f"del_btn_{index}")                
            st.divider()
            cols = st.columns(3)

            if sum(error_list)==0:
                cols[1].button("Proceed to upload",
                               disabled=False,
                               type='primary',
                               on_click=lambda : session.upload_kirtan({'process_step_2':True}))
               
                # final_upload
            else:
                cols[1].button("some fields are empty in bookmark",
                               disabled=True)
            # ------------------------------------
            if session.upload_kirtan['process_step_2']:
                # 'kf_available':False,
                # 'kirtan_info': None,
                # 'process_step_1':False,
                # 'bookmark_list': [{'start_time':0,'start_time_raw':0,'display_time':'0m 0s','tune_hint':''}],
                # 'process_step_2':False
                
                final_upload = {
                    'kirtan_info':session.upload_kirtan['kirtan_info'],
                    'bookmark_list':session.upload_kirtan['bookmark_list'],
                }
                is_success = upload_kirtan_now(final_upload)
                if is_success:
                    session.upload_kirtan.update({
                        'kf_available':False,
                        'kirtan_info': None,
                        'process_step_1':False,
                        'bookmark_list': [{'start_time':0,'start_time_raw':0,'display_time':'0m 0s','tune_hint':''}],
                        'process_step_2':False
                    })

# ----------- Browse Kirtans ------------
def browse_kirtans():
    st.title("Browse Kirtans")
    # Assume a function get_all_kirtans() that fetches saved data
    kirtans = ["Kirtan 1", "Kirtan 2", "Kirtan 3"]  # Replace with real data

    selected_kirtan = st.selectbox("Choose a Kirtan", kirtans)

    if selected_kirtan:
        st.write(f"### Selected Kirtan: {selected_kirtan}")
        # Assume get_kirtan_bookmarks() fetches tune timestamps
        bookmarks = [(30, "Tune 1"), (90, "Tune 2")]  # Replace with actual bookmarks

        for time, label in bookmarks:
            if st.button(f"Play {label} ({time}s)"):
                st.audio("example.mp3", start_time=time)  # Replace with actual file

# ----------- add an essence ------------
def add_new_essence():
    pass
# ----------- browse essence ------------
def browse_essence():
    pass

# global css
st.markdown(
    """
    <style>
    [data-testid="stNumberInputStepDown"],
    [data-testid="stNumberInputStepUp"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------- Main App ------------
def main():
    user_cred = session.login['user_creds']
    with st.sidebar:
        st.markdown(f"## :rainbow[Hare Krishna] :gray[{user_cred['full_name']}]")
        st.divider()
        st.subheader(":blue[Choose an action]")
        access_list = user_cred['role_list']
        
        def update_page(page):
            session.navigate.update({'active_page':page})

        if 'admin' in access_list:
            st.button("Approve Pending",key='pending',
                      on_click=update_page,args=['approve'])
            
        st.button("Explore Kirtan",key='explore',
                on_click=update_page,args=['kirtans'])
        
        # if 'uploader' in access_list:
        st.button("Upload New",key='upload',
                on_click=update_page,args=['upload'])


            
        

    # ==============================================================
    active_page = session.navigate['active_page']
    page_map = {'kirtans':browse_kirtans,
                'approve':approve_regs,
                'upload':upload_kirtan,
                }
    
    if not active_page:
        st.warning("Please select a page")

    else :
        page_map[active_page]()


if session.login['is_logged_in']:
    main()
else:
    login_page()