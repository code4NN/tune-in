import streamlit as st
import tempfile
import os
import subprocess
import io

def is_valid_timestamp(input_time,muted=False):
    """
    returns (time_is_valid, msg to show, duration)
    """
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

def trim_audio(src_type,src, start_time, duration):
    input_file_path = None
    if src_type =='buffer':
         with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(src.read())
            input_file_path = tmp.name
    else :
        input_file_path = src
    
    try:
    
        # ffmpeg setup
        ffmpeg_path = r"./ffmpeg_for_linux/ffmpeg_binary/ffmpeg-7.0.2-amd64-static/ffmpeg"
        os.chmod(ffmpeg_path, 0o755)

        output_buffer = io.BytesIO()

        command = [
            ffmpeg_path,
            '-i', input_file_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-f', 'mp3',
            '-'
        ]

        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        output_buffer.write(process.stdout)
        output_buffer.seek(0)
    except Exception as e:
        st.error(e)
    
    finally:
        os.remove(input_file_path)


    return output_buffer