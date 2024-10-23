import streamlit as st
from flowise import Flowise, PredictionData
import json

# Flowise app base url
base_url = st.secrets.get("APP_URL", "https://app.flowise.ai")

# Chatflow/Agentflow ID
flow_id = st.secrets.get("FLOW_ID", "a5efc1c7-f458-429d-9dfc-e201c19e2c31")

# Show title and description.
st.title("💬 Flowise Streamlit Chat")
st.write(
    "This is a simple chatbot that uses Flowise Python SDK"
)

# Create a Flowise client.
client = Flowise(base_url=base_url)

# Initialize session state variables for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

def generate_response(prompt: str):
    print('generating response')
    completion = client.create_prediction(
        PredictionData(
            chatflowId=flow_id,
            question=prompt,
            overrideConfig={
                "sessionId": "session1234"
            },
            streaming=True
        )
    )

    assistant_response = ""
    reasoning_steps = []

    for chunk in completion:
        print(chunk)
        parsed_chunk = json.loads(chunk)

        # Handle agent reasoning events
        if parsed_chunk['event'] == 'agentReasoning':
            reasoning_data = parsed_chunk.get('data', [])
            for reasoning_event in reasoning_data:
                agent_name = reasoning_event.get('agentName', 'Agent')
                messages = reasoning_event.get('messages', [])
                instructions = reasoning_event.get('instructions', '')
                reasoning_step = f"**{agent_name} Reasoning:**\n"
                if messages:
                    reasoning_step += '\n'.join(messages)
                if instructions:
                    reasoning_step += f"\n**Instructions:** {instructions}"
                reasoning_steps.append(reasoning_step)
            # Combine reasoning steps
            reasoning_text = '\n\n'.join(reasoning_steps)
            # Store reasoning in session state
            st.session_state["current_reasoning"] = reasoning_text
        # Handle token events (assistant's response)
        elif parsed_chunk['event'] == 'token' and parsed_chunk['data'] != '':
            assistant_response += parsed_chunk['data']
            yield assistant_response  # Yield the entire assistant response so far

    # Store the final assistant response
    st.session_state["current_response"] = assistant_response

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # If the message is from the assistant and has reasoning
        if message["role"] == "assistant" and "reasoning" in message:
            with st.expander("Show Agent Reasoning"):
                st.markdown(message["reasoning"])

# Create a chat input field
if prompt := st.chat_input("Type your message here..."):

    # Store and display the user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display the assistant's response
    with st.chat_message("assistant"):
        # Initialize placeholders
        assistant_response_text = ''
        response_placeholder = st.empty()
        reasoning_placeholder = st.empty()

        # Initialize current reasoning
        st.session_state["current_reasoning"] = ""

        # Generate response
        response_stream = generate_response(prompt)
        for response_chunk in response_stream:
            assistant_response_text = response_chunk
            # Update the assistant's response
            response_placeholder.markdown(assistant_response_text)
            # If reasoning is available, display it
            if st.session_state.get("current_reasoning"):
                with reasoning_placeholder.expander("Show Agent Reasoning"):
                    st.markdown(st.session_state["current_reasoning"])

        # Append the assistant's message and reasoning to session state
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response_text,
            "reasoning": st.session_state.get("current_reasoning", "")
        })
