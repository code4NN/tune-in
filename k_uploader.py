import streamlit as st
import pandas as pd

from audio_processor import is_valid_timestamp
from audio_processor import trim_audio


def get_kirtan_info(uploaded_kirtan):
    # ================================================================
    session = st.session_state['session']

    # ------------------------ get the start and end of kirtan time

    with st.popover("Time format guide"):
                    st.markdown("* last 2 digit of integer are considered as seconds. and remaining(if any) as minutes")
                    st.dataframe(pd.DataFrame([
                              [1,"1 s"],
                              [16,"16 s"],
                              [108,"1 min 8 s"],
                              [1600,"16 min 0 s"]
                              ],columns=['input','inferred time']),
                             hide_index=True)
    cols = st.columns(2)
    st.markdown("#### Full audio")
        
    with cols[0]:
        start_time = st.number_input("start time", min_value=0)
        start_time_response = is_valid_timestamp(start_time)
        start_time = start_time_response[1]['duration']
        
    with cols[1]:
        end_time = st.number_input("end time", min_value=start_time)
        end_time_response = is_valid_timestamp(end_time)
        end_time = end_time_response[1]['duration']
    
        
    duration = end_time - start_time
    
    if duration > 30*60:
        st.error("Duration cannot exceed 30 minutes")
    elif duration < 60:
        st.error("Duration cannot be less than one minute")
    elif (not start_time_response[0]) or (not end_time_response[0]):
        pass
    else:
        def clip_audio():
            session.ux.update({'clip_to_preview_exec':True})
        st.button("Clip Audio and Preview",on_click=clip_audio)
        if session.ux.get('clip_to_preview_exec',False):
            session.ux.update({'clip_to_preview_exec':False})
            with st.spinner("Clipping..."):
                trimed_audio = trim_audio(src_type='buffer',src=uploaded_kirtan,
                           start_time=start_time,
                           duration=duration)
                session.upload_kirtan['clipped_audio'] = trimed_audio
        
        if session.upload_kirtan['clipped_audio'] is not None:
            st.markdown("Selected Kirtan")
            st.audio(session.upload_kirtan['clipped_audio'],format='audio/wav')
            
            
                
    
    st.divider()
    # ================================================================
    # ------------------------ get the singer and how many beats and occasion
    cols = st.columns(2)
    
    with cols[0]:
        current_singer_df = session.conn.upl_get_singer_list().copy()
        current_singer_df.insert(0,'select',False)
        singer = st.data_editor(current_singer_df,
                                column_order=['select','full_name'],
                                column_config={'select':st.column_config.CheckboxColumn(label="Select",width='small',disabled=False),
                                               'full_name':st.column_config.TextColumn(label="Name",width='large',disabled=True)},
                                hide_index=True).query("select==True")
        
        with st.popover("Wish to add a name",use_container_width=True):
            st.markdown("### :green[Adding a new Singer]")
            info_holder = st.empty()

            new_name = st.text_input("Full Name",max_chars=50,key='new_name').strip()
            if new_name.replace(" ","").lower() in current_singer_df.full_name.str.replace(" ","").str.lower().tolist():
                st.caption(f":red[{new_name} already exists]")
                new_name = ''
            new_aashram = st.segmented_control("Prabhuji/Maharaj",options=['Maharaj','Prabhuji'],selection_mode='single')
            new_nickname = st.text_input("Short Name",max_chars=10,key='new_short_name').strip()
            
            if new_nickname.replace(" ","").lower() in current_singer_df.short_name.str.replace(" ","").str.lower().tolist():
                st.caption(f":red[{new_nickname} is already taken]")
                st.caption("Please enter a unique Short Name")

            if new_name and new_aashram and new_nickname:
                def onboard_new_singer():
                    session.ux.update({'onboard_new_singer_exec':True})
                    session.ux.update({"payload":{'full_name':new_name,
                                                  'short_name':new_nickname}})
                    st.session_state['new_name'] = ''
                    st.session_state['new_short_name'] = ''
                st.button(f"Add {new_nickname}",on_click=onboard_new_singer)
            
            if session.ux.get("onboard_new_singer_exec",False):
                session.ux.update({'onboard_new_singer_exec':False})
                payload = {'hg_hh':new_aashram,
                           **session.ux['payload']
                            # 'full_name':new_name,
                            # 'short_name':new_nickname
                            }
                try:
                    session.conn.upl_enroll_new_singer(payload)
                    info_holder.success("Added to singer list")
                    st.toast(f"Successfully added {new_name} to singer list")
                    st.rerun()

                except Exception as e :
                    info_holder.error("Some error occured")
                    st.error(e)

        if singer.shape[0]!=1:
            st.warning("Please select exactly one singer")
            singer = []
        else:
            singer = list(singer.to_dict(orient='index').values())[0]
            st.caption(singer['full_name'])
            singer = singer['short_name']
            st.write(singer)
        #     st.warning("Please select a singer")
            
    with cols[1]:
        tune_name = st.text_input("title").strip()
        if not tune_name:
            st.caption(":red[please enter a title]")

        OCCASION_LIST = ['Morning Program', 'Guru Puja', 'Before Class', 'Shayan Kirtan','Festival','Other']
        occasion = st.segmented_control(":blue[Kirtan Occasion]",options=OCCASION_LIST,selection_mode='single')
        if not occasion:
            st.caption(":red[Please select one selection]")
        
        BEAT_LIST = ['2 beat','3 beat','bhajani','more beats']
        beat_count = st.segmented_control(":violet[includes beats (multi selection)]",options=BEAT_LIST,selection_mode='multi')
        if not beat_count:
            st.caption(":red[Please select at least one selection]")

        PACE_LIST = ['slow','medium','fast']
        # st.markdown()
        pace = st.segmented_control(':violet[Kirtan pace (multi selection)]',options=PACE_LIST,selection_mode='multi')
        if not pace:
            st.caption(":red[please select something!!]")

    # ==============================================================
    # -------------------------- validate and return
    if singer == '':
        st.error("Singer cannot be empty")
        return False,{}
    elif (not start_time_response[0]) or (not end_time_response[0]):
        return False, {}
    
    
    else:
        return True,{"start_time":start_time,
                 "end_time":end_time,
                 "duration":duration,
                 "singer":singer,
                 "tune_name":tune_name}
    
