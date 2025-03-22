import streamlit as st

def is_valid_timestamp(input_time,muted=False):
    """
    returns (time_is_valid, msg to show, duration)"""
    input_time = str(input_time)
    # st.caption(input_time)
    
    time_min,time_sec = None,None
    if len(input_time) in [1,2]:
        # seconds
        time_min,time_sec = 0,int(input_time)
    else:
        time_min,time_sec = int(input_time[:-2]), int(input_time[-2:])
    
    duration_seconds = sum([time_min*60,time_sec])
    
    if time_sec > 59:
        if not muted:
            st.caption(f"### :red[second ({time_sec}) cannot exceed 59]")
        return False,{"display_text":'',"duration":-1}
            
    else:
        return True, {"display_text":f":green[{time_min}m {time_sec}s]",
                      "duration":duration_seconds}

def trim_audio(audio_file, start_time, duration):
    return 'trimmed audio'