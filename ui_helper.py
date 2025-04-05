import streamlit as st
from audio_manager import is_valid_timestamp

import re
from urllib.parse import urlparse, parse_qs


def get_kirtan_info():
    # ================================================================
    # ------------------------ get the start and end of kirtan time
    cols = st.columns(2)
        
    with cols[0]:
        start_time = st.number_input("start time", min_value=0)
        start_time_response = is_valid_timestamp(start_time)
        start_time = start_time_response[1]['duration']
        
    with cols[1]:
        end_time = st.number_input("end time", min_value=start_time)
        end_time_response = is_valid_timestamp(end_time)
        end_time = end_time_response[1]['duration']
        
    duration = end_time - start_time
    
    if duration > 20*60:
        st.error("Duration cannot exceed 20 minutes")
    st.divider()
    # ================================================================
    # ------------------------ get the singer and tune name
    cols = st.columns(2)
    
    with cols[0]:
        SINGER_LIST = ['HH RNSM','other']
        singer = st.radio("Singer",options=SINGER_LIST)
        if singer =='other':
            singer = st.text_input("Singer").strip()
            
    with cols[1]:
        tune_name = st.text_input("Tune Name").strip()

    # ==============================================================
    # -------------------------- validate and return
    if singer == '':
        st.error("Singer cannot be empty")
        return False,{}
    elif tune_name == '':
        st.error("Tune Name cannot be empty")
        return False,{}
    elif (not start_time_response[0]) or (not end_time_response[0]):
        return False, {}
    
    else:
        return True,{"start_time":start_time,
                 "end_time":end_time,
                 "duration":duration,
                 "singer":singer,
                 "tune_name":tune_name}
    
def get_video_id():
    url = st.text_input("Enter youtube url")
    video_id = extract_youtube_video_id(url)
    return video_id



def extract_youtube_video_id(url):
    parsed_url = urlparse(url)

    # youtu.be/<id>
    if 'youtu.be' in parsed_url.netloc:
        return parsed_url.path.lstrip('/')

    # youtube.com/embed/<id>
    if '/embed/' in parsed_url.path:
        return parsed_url.path.split('/embed/')[1]

    # youtube.com/shorts/<id>
    if '/shorts/' in parsed_url.path:
        return parsed_url.path.split('/shorts/')[1]

    # youtube.com/live/<id>
    if '/live/' in parsed_url.path:
        return parsed_url.path.split('/live/')[1]

    # youtube.com/watch?v=<id>
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        query_params = parse_qs(parsed_url.query)
        return query_params.get('v', [None])[0]

    return None