import streamlit as st
from backend.main import build_rag_graph
from langchain_core.messages import HumanMessage

st.set_page_config(
    page_title="Heart Failure CDSS",
    layout="centered",
    initial_sidebar_state="expanded"
)
st.title("Heart Failure Management CDSS - 2022 AHA/ACC/HFSA")

# Initialize chat history
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# Display previous messages
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# User input
user_input = st.chat_input('Type here')

if user_input:
    # Add user message to session
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    # Build LangGraph
    rag_graph = build_rag_graph()
    config = {'configurable': {'thread_id': 'thread-1'}}
    initial_state = {
        'query': [HumanMessage(content=user_input)],
        'guideline_path': 'data/HF_Guideline.pdf'
    }

    # Stream assistant response with spinner
    with st.spinner("Processing and generating response..."):
            response = rag_graph.invoke(input=initial_state, config=config)
            output = response['messages'][-1].content
            st.session_state['message_history'].append({'role': 'assistant', 'content': output})
            with st.chat_message('assistant'):
                st.markdown(output)


    #         ai_message = st.write_stream(
    #             message_chunk.content
    #             for message_chunk, metadata in rag_graph.stream(
    #                 input=initial_state,
    #                 config=config,
    #                 stream_mode='messages'
    #             )
    #         )
    # # # Add assistant response to session
    # st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
