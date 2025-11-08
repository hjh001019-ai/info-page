{\rtf1\ansi\ansicpg949\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import os\
import csv\
import io\
from datetime import datetime\
from google import genai\
from google.genai import types\
from google.genai.errors import APIError\
\
# --- \uc0\u49444 \u51221  \u48143  \u52488 \u44592 \u54868  ---\
\
# \uc0\u54168 \u51060 \u51648  \u44592 \u48376  \u49444 \u51221 \
st.set_page_config(page_title="AI \uc0\u44256 \u44061  \u51025 \u45824  \u52311 \u48391 ", page_icon="\u55357 \u57037 \u65039 ", layout="wide")\
\
# \uc0\u49324 \u50857  \u44032 \u45733 \u54620  \u47784 \u45944  \u47785 \u47197  (exp \u47784 \u45944  \u51228 \u50808 )\
AVAILABLE_MODELS = [\
    "gemini-2.0-flash", \
    "gemini-2.0-pro",\
    "gemini-2.5-flash", \
    "gemini-2.5-pro",\
]\
\
# \uc0\u49884 \u49828 \u53596  \u54532 \u47212 \u54532 \u53944  (\u50836 \u52397 \u49324 \u54637  \u51456 \u49688 )\
SYSTEM_PROMPT = """\
1) \uc0\u49324 \u50857 \u51088 \u45716  \u49660 \u54609 \u47792  \u44396 \u47588 \u44284 \u51221 \u50640 \u49436  \u44202 \u51008  \u48520 \u54200 /\u48520 \u47564 \u51012  \u50616 \u44553 \u54633 \u45768 \u45796 . \u51221 \u51473 \u54616 \u44256  \u44277 \u44048  \u50612 \u47536  \u47568 \u53804 \u47196  \u51025 \u45813 \u54616 \u49464 \u50836 .\
2) \uc0\u49324 \u50857 \u51088 \u51032  \u48520 \u54200 \u49324 \u54637 \u51012  \u44396 \u52404 \u51201 \u51004 \u47196  \u51221 \u47532 \u54616 \u50668 (\u47924 \u50631 \u51060 /\u50616 \u51228 /\u50612 \u46356 \u49436 /\u50612 \u46523 \u44172 ) \u49688 \u51665 \u54616 \u44256 , \u51060 \u47484  \u44256 \u44061  \u51025 \u45824  \u45812 \u45817 \u51088 \u50640 \u44172  \u51204 \u45804 \u54620 \u45796 \u45716  \u52712 \u51648 \u47196  \u50504 \u45236 \u54616 \u49464 \u50836 .\
3) \uc0\u47560 \u51648 \u47561 \u50640 \u45716  \u45812 \u45817 \u51088  \u54869 \u51064  \u54980  \u54924 \u49888 \u51012  \u50948 \u54644  \u51060 \u47700 \u51068  \u51452 \u49548 \u47484  \u50836 \u52397 \u54616 \u49464 \u50836 .\
\uc0\u47564 \u51068  \u49324 \u50857 \u51088 \u44032  \u50672 \u46973  \u51228 \u44277 \u51012  \u50896 \u52824  \u50506 \u51004 \u47732 : \'93\u51396 \u49569 \u54616 \u51648 \u47564 , \u50672 \u46973 \u52376  \u51221 \u48372 \u47484  \u48155 \u51648  \u47803 \u54616 \u50668  \u45812 \u45817 \u51088 \u51032  \u44160 \u53664  \u45236 \u50857 \u51012  \u48155 \u51004 \u49892  \u49688  \u50630 \u50612 \u50836 .\'94\u46972 \u44256  \u51221 \u51473 \u55176  \u50504 \u45236 \u54616 \u49464 \u50836 .\
"""\
\
# \uc0\u45824 \u54868  \u44592 \u47197  \u50976 \u51648  \u44600 \u51060  (\u50836 \u52397  \u49324 \u54637 \u50640  \u46384 \u46972  6\u53556 \u51004 \u47196  \u49444 \u51221 )\
# history_limit = 6 * 2 (\uc0\u49324 \u50857 \u51088  + AI \u53556 )\
CONTEXT_WINDOW_LIMIT = 12\
\
# --- \uc0\u49464 \u49496  \u49345 \u53468  \u44288 \u47532  ---\
\
if 'chat_history' not in st.session_state:\
    # \uc0\u51204 \u52404  \u45824 \u54868  \u55176 \u49828 \u53664 \u47532  (\u54868 \u47732  \u54364 \u49884  \u48143  API \u51204 \u49569 \u50857 )\
    st.session_state.chat_history = [] \
if 'conversation_log' not in st.session_state:\
    # CSV \uc0\u44592 \u47197 \u50857  \u49345 \u49464  \u47196 \u44536 \
    st.session_state.conversation_log = [] \
if 'session_id' not in st.session_state:\
    # \uc0\u49464 \u49496  \u49885 \u48324 \u51088  \u49373 \u49457 \
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")\
if 'retry_count' not in st.session_state:\
    # 429 \uc0\u51116 \u49884 \u46020  \u52852 \u50868 \u53552 \
    st.session_state.retry_count = 0\
if 'log_enabled' not in st.session_state:\
    # CSV \uc0\u51088 \u46041  \u44592 \u47197  \u50741 \u49496 \
    st.session_state.log_enabled = True\
\
# --- \uc0\u50976 \u54008 \u47532 \u54000  \u54632 \u49688  ---\
\
def log_message(role, content):\
    """\uc0\u45824 \u54868  \u45236 \u50857 \u51012  CSV \u44592 \u47197 \u50857  \u47196 \u44536 \u50640  \u52628 \u44032 """\
    st.session_state.conversation_log.append(\{\
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),\
        "session_id": st.session_state.session_id,\
        "role": role,\
        "content": content\
    \})\
\
def create_csv_file():\
    """\uc0\u49464 \u49496  \u49345 \u53468 \u51032  \u47196 \u44536 \u47484  \u44592 \u48152 \u51004 \u47196  CSV \u54028 \u51068  \u49373 \u49457  (\u45796 \u50868 \u47196 \u46300 \u50857 )"""\
    output = io.StringIO()\
    fieldnames = ["timestamp", "session_id", "role", "content"]\
    writer = csv.DictWriter(output, fieldnames=fieldnames)\
    \
    writer.writeheader()\
    writer.writerows(st.session_state.conversation_log)\
    \
    return output.getvalue().encode('utf-8')\
\
def new_chat_session():\
    """\uc0\u45824 \u54868  \u52488 \u44592 \u54868  \u48143  \u49352  \u49464 \u49496  \u49884 \u51089 """\
    st.session_state.chat_history = []\
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")\
    st.session_state.retry_count = 0\
    st.rerun()\
\
def get_client(api_key):\
    """Gemini \uc0\u53364 \u46972 \u51060 \u50616 \u53944  \u52488 \u44592 \u54868 """\
    try:\
        return genai.Client(api_key=api_key)\
    except Exception as e:\
        st.error(f"\uc0\u53364 \u46972 \u51060 \u50616 \u53944  \u52488 \u44592 \u54868  \u50724 \u47448 : \{e\}")\
        return None\
\
# --- UI \uc0\u52980 \u54252 \u45324 \u53944  ---\
\
def sidebar_config():\
    """\uc0\u49324 \u51060 \u46300 \u48148  \u49444 \u51221  \u48143  \u51221 \u48372  \u54364 \u49884 """\
    with st.sidebar:\
        st.title("\uc0\u55357 \u57037 \u65039  \u52311 \u48391  \u49444 \u51221 ")\
        \
        # 1. \uc0\u47784 \u45944  \u49440 \u53469 \
        st.session_state.selected_model = st.selectbox(\
            "\uc0\u44592 \u48376  \u47784 \u45944  \u49440 \u53469 ",\
            AVAILABLE_MODELS,\
            index=AVAILABLE_MODELS.index("gemini-2.0-flash")\
        )\
        st.info(f"\uc0\u49440 \u53469 \u46108  \u47784 \u45944 : **\{st.session_state.selected_model\}**")\
\
        # 2. API \uc0\u53412  \u51077 \u47141 \
        api_key = st.secrets.get("GEMINI_API_KEY")\
        if not api_key:\
            api_key = st.text_input(\
                "Gemini API Key \uc0\u51077 \u47141 ", \
                type="password",\
                placeholder="st.secrets['GEMINI_API_KEY']\uc0\u51060  \u49444 \u51221 \u46104 \u51648  \u50506 \u50520 \u49845 \u45768 \u45796 ."\
            )\
        \
        # 3. \uc0\u49464 \u49496  \u51221 \u48372 \
        st.subheader("\uc0\u49464 \u49496  \u51221 \u48372 ")\
        st.caption(f"**\uc0\u49464 \u49496  ID**: `\{st.session_state.session_id\}`")\
        st.caption(f"**\uc0\u54788 \u51116  \u45824 \u54868  \u53556 **: \{len(st.session_state.chat_history)//2\}")\
        st.caption(f"**429 \uc0\u51116 \u49884 \u46020  \u54943 \u49688 **: \{st.session_state.retry_count\}")\
\
        st.markdown("---")\
        \
        # 4. \uc0\u44592 \u45733  \u48260 \u53948 \
        st.button("\uc0\u55357 \u56580  \u45824 \u54868  \u52488 \u44592 \u54868 ", on_click=new_chat_session, help="\u54788 \u51116  \u45824 \u54868 \u47484  \u50756 \u51204 \u55176  \u52488 \u44592 \u54868 \u54633 \u45768 \u45796 .")\
        \
        # 5. CSV \uc0\u51088 \u46041  \u44592 \u47197  \u50741 \u49496 \
        st.session_state.log_enabled = st.checkbox("CSV \uc0\u51088 \u46041  \u44592 \u47197  \u54876 \u49457 \u54868 ", value=st.session_state.log_enabled)\
\
        # 6. \uc0\u47196 \u44536  \u45796 \u50868 \u47196 \u46300 \
        if st.session_state.conversation_log:\
            csv_data = create_csv_file()\
            st.download_button(\
                label="\uc0\u11015 \u65039  \u51204 \u52404  \u47196 \u44536  CSV \u45796 \u50868 \u47196 \u46300 ",\
                data=csv_data,\
                file_name=f"chatbot_log_\{st.session_state.session_id\}.csv",\
                mime="text/csv",\
                help="\uc0\u54788 \u51116 \u44620 \u51648 \u51032  \u47784 \u46304  \u45824 \u54868  \u47196 \u44536 \u47484  CSV \u54028 \u51068 \u47196  \u51200 \u51109 \u54633 \u45768 \u45796 ."\
            )\
            \
        return api_key\
\
# --- \uc0\u47700 \u51064  \u52311 \u48391  \u47196 \u51649  ---\
\
def handle_chat_input(api_key):\
    """\uc0\u49324 \u50857 \u51088  \u51077 \u47141  \u52376 \u47532  \u48143  API \u54840 \u52636 """\
    \
    # 1. \uc0\u53364 \u46972 \u51060 \u50616 \u53944  \u52488 \u44592 \u54868  \u44160 \u51613 \
    client = get_client(api_key)\
    if not api_key or not client:\
        st.warning("Gemini API Key\uc0\u47484  \u51077 \u47141 \u54616 \u44144 \u45208  secrets\u50640  \u49444 \u51221 \u54644 \u50556  \u52311 \u48391 \u51060  \u51089 \u46041 \u54633 \u45768 \u45796 .")\
        return\
\
    # 2. \uc0\u49324 \u50857 \u51088  \u51077 \u47141  \u52376 \u47532 \
    if user_prompt := st.chat_input("\uc0\u48520 \u54200 \u54616 \u49888  \u49324 \u54637 \u51012  \u47568 \u50432 \u54644  \u51452 \u49464 \u50836 ."):\
        \
        # \uc0\u49324 \u50857 \u51088  \u47700 \u49884 \u51648  \u54364 \u49884  \u48143  \u44592 \u47197 \
        st.session_state.chat_history.append(types.Content(role="user", parts=[types.Part.from_text(user_prompt)]))\
        if st.session_state.log_enabled:\
            log_message("user", user_prompt)\
        \
        # \uc0\u45824 \u54868  \u45236 \u50857  \u54364 \u49884 \
        with st.chat_message("user"):\
            st.markdown(user_prompt)\
\
        # 3. \uc0\u52968 \u53581 \u49828 \u53944  \u51228 \u54620  \u54869 \u51064  \u48143  \u51116 \u49884 \u51089  \u47196 \u51649  (429/\u44596  \u45824 \u54868  \u51116 \u49884 \u46020  \u47196 \u51649 )\
        \
        # \uc0\u54788 \u51116  history\u50640 \u49436  \u49884 \u49828 \u53596  \u54532 \u47212 \u54532 \u53944 \u47484  \u51228 \u50808 \u54620  \u49324 \u50857 \u51088 /\u47784 \u45944 \u51032  \u45824 \u54868  \u49688 \
        current_turns = len(st.session_state.chat_history)\
        \
        if current_turns >= CONTEXT_WINDOW_LIMIT:\
            st.session_state.retry_count += 1\
            \
            # API \uc0\u54840 \u52636  \u49884  CONTEXT_WINDOW_LIMIT - 1\u44060 \u47564  \u49324 \u50857  (\u44032 \u51109  \u52572 \u44540  6\u53556 )\
            # -1\uc0\u51008  user_prompt\u44032  \u51060 \u48120  history\u50640  \u52628 \u44032 \u46104 \u50632 \u44592  \u46412 \u47928 .\
            history_slice = st.session_state.chat_history[-(CONTEXT_WINDOW_LIMIT - 1):]\
            \
            st.warning(f"\uc0\u9888 \u65039  \u45824 \u54868 \u44032  \u44600 \u50612 \u51256  (\{current_turns/2\}\u53556 ), \u52968 \u53581 \u49828 \u53944  \u50976 \u51648 \u47484  \u50948 \u54644  \u52572 \u44540  6\u53556 \u47564  \u49324 \u50857 \u54616 \u50668  \u45813 \u48320 \u51012  \u49373 \u49457 \u54633 \u45768 \u45796 . (429 \u51116 \u49884 \u46020  \u51221 \u52293 )")\
        else:\
            history_slice = st.session_state.chat_history\
\
        # 4. API \uc0\u54840 \u52636 \
        with st.chat_message("assistant"):\
            with st.spinner("\uc0\u51025 \u45813  \u49373 \u49457  \u51473 \u51077 \u45768 \u45796 ..."):\
                try:\
                    # History \uc0\u49836 \u46972 \u51060 \u49828 \u50640  \u52572 \u49888  \u49324 \u50857 \u51088  \u51077 \u47141 \u51060  \u54252 \u54632 \u46104 \u50612  \u51080 \u51004 \u48064 \u47196 , \
                    # history_slice\uc0\u47484  \u48148 \u47196  contents\u47196  \u49324 \u50857 \u54633 \u45768 \u45796 .\
                    \
                    config = types.GenerateContentConfig(\
                        system_instruction=SYSTEM_PROMPT\
                    )\
                    \
                    response = client.models.generate_content(\
                        model=st.session_state.selected_model,\
                        contents=history_slice,\
                        config=config\
                    )\
                    \
                    ai_response_text = response.text\
                    st.markdown(ai_response_text)\
                    \
                    # AI \uc0\u47700 \u49884 \u51648  \u44592 \u47197  \u48143  \u55176 \u49828 \u53664 \u47532  \u50629 \u45936 \u51060 \u53944 \
                    st.session_state.chat_history.append(types.Content(role="model", parts=[types.Part.from_text(ai_response_text)]))\
                    if st.session_state.log_enabled:\
                        log_message("model", ai_response_text)\
\
                except APIError as e:\
                    error_msg = f"API \uc0\u50724 \u47448 \u44032  \u48156 \u49373 \u54664 \u49845 \u45768 \u45796 . (Code: \{e.status_code\}) \u51396 \u49569 \u54616 \u51648 \u47564 , \u51104 \u49884  \u54980  \u45796 \u49884  \u49884 \u46020 \u54644  \u51452 \u49464 \u50836 . \u49345 \u49464  \u50724 \u47448 : \{e.message\}"\
                    st.error(error_msg)\
                    st.session_state.chat_history.pop() # \uc0\u50724 \u47448  \u48156 \u49373  \u49884  \u49324 \u50857 \u51088  \u51077 \u47141  \u51228 \u44144 \
                    if st.session_state.log_enabled:\
                        log_message("system_error", error_msg)\
                except Exception as e:\
                    error_msg = f"\uc0\u50696 \u49345 \u52824  \u47803 \u54620  \u50724 \u47448 \u44032  \u48156 \u49373 \u54664 \u49845 \u45768 \u45796 : \{e\}"\
                    st.error(error_msg)\
                    st.session_state.chat_history.pop()\
                    if st.session_state.log_enabled:\
                        log_message("system_error", error_msg)\
\
# --- \uc0\u47700 \u51064  \u54632 \u49688  ---\
\
def main():\
    st.title("\uc0\u55357 \u57037 \u65039  AI \u44256 \u44061  \u48520 \u54200 \u49324 \u54637  \u51217 \u49688  \u52311 \u48391 ")\
    st.markdown("""\
        **\uc0\u54872 \u50689 \u54633 \u45768 \u45796 .** \u49660 \u54609 \u47792  \u51060 \u50857  \u51473  \u44202 \u51004 \u49888  \u48520 \u54200  \u49324 \u54637 \u50640  \u45824 \u54644  \u51221 \u51473 \u54616 \u44256  \u44277 \u44048  \u50612 \u47536  \u45824 \u51025 \u51012  \u51228 \u44277 \u54616 \u47728 , \
        \uc0\u45812 \u45817 \u51088 \u50640 \u44172  \u51204 \u45804 \u54624  \u49688  \u51080 \u46020 \u47197  \u44396 \u52404 \u51201 \u51064  \u51221 \u48372 \u47484  \u49688 \u51665 \u54633 \u45768 \u45796 .\
    """)\
\
    # \uc0\u49324 \u51060 \u46300 \u48148  \u49444 \u51221  \u47196 \u46300  \u48143  API \u53412  \u44160 \u51613 \
    api_key = sidebar_config()\
\
    # \uc0\u44592 \u51316  \u45824 \u54868  \u45236 \u50857  \u54364 \u49884 \
    for message in st.session_state.chat_history:\
        # types.Content \uc0\u44061 \u52404 \u51032  role\u51012  \u49324 \u50857 \u54616 \u50668  \u47700 \u49884 \u51648  \u54364 \u49884 \
        role = "user" if message.role == "user" else "assistant"\
        with st.chat_message(role):\
            # parts\uc0\u45716  list\u51060 \u48064 \u47196  \u52395  \u48264 \u51704  \u53581 \u49828 \u53944  \u54028 \u53944 \u47484  \u44032 \u51256 \u50741 \u45768 \u45796 .\
            text_content = message.parts[0].text if message.parts and hasattr(message.parts[0], 'text') else ""\
            st.markdown(text_content)\
\
    # \uc0\u49324 \u50857 \u51088  \u51077 \u47141  \u52376 \u47532 \
    handle_chat_input(api_key)\
\
if __name__ == "__main__":\
    main()}