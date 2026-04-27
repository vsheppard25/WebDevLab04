import streamlit as st
from google import genai

st.set_page_config(page_title="Fruit Bot", page_icon="🥝")

st.title("🥝 Fruit Bot")

#create the chat
def build_chat(client):
    history = []

    for msg in st.session_state.messages[-10:]:
        if msg["role"] == "system":
            continue

        gemini_role = "model" if msg["role"] == "assistant" else "user"
        history.append({
            "role": gemini_role,
            "parts": [{"text": msg["content"]}]
        })

    return client.chats.create(
        model="gemini-2.0-flash",
        history=history
    )

# system prompt
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                """
                You are a fruit themed chatbot.
                Guidlines:
                - If the prompt is not related to fruit, kindly ask to connect it back to fruit.
                - suggest recipes, explain nutrition in simple terms, and have normal conversation
                - Keep a school-appropriate tone and remain helpful and concise, but always keep a light fruit flavor in your tone.
                """
            )
        },
        {
            "role": "assistant",
            "content": (
                "Hi! Lets chat about fruit 🍎🍌🍇. Ask me anything about fruits, "
                "snacks, smoothies, recipes, or fun facts"
            )
        },
    ]

# display chat
for message in st.session_state.messages:
    if message["role"] == "system":
        continue # skip system prompt
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# handle new user input

prompt = st.chat_input("Type your fruit-themed message here...")

if prompt:
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        error_message = (
            "Provide an API key to enable access to Gemini"
        )
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        with st.chat_message("assistant"):
            st.error(error_message)
    else:
        try:
            @st.cache_resource
            def get_gemini_client():
                return genai.Client(api_key=api_key)
            client = get_gemini_client()
            chat = build_chat(client)

            # add context to the prompt to make sure gemini stays friendly
            themed_prompt = (
                f"Stay in a fruit-themed tone while answering this message:\n\n{prompt}"
            )

            response = chat.send_message(themed_prompt)

            # make sure acutal text is written
            assistant_text = response.text.strip() if response.text else (
                "Sorry, I couldn't generate a fruit-filled reply for that. "
                "Try asking in a different way!"
            )

        except Exception as e:
            # use try-except to catch API errors like rate limits, safety issues, or req quote
            error_text = str(e).lower()

            if "rate" in error_text or "quota" in error_text or "429" in error_text:
                assistant_text = (
                    "Too many requests hit the fruit stand at once 🍍. "
                    "Please wait a moment and try again."
                )
            elif "api key" in error_text or "permission" in error_text or "auth" in error_text:
                assistant_text = (
                    "There seems to be a problem with the Gemini API key 🍊. "
                )
            elif "safety" in error_text or "blocked" in error_text:
                assistant_text = (
                    "That request got blocked for safety reasons 🍒. "
                    "Please rephrase it."
                )
            else:
                assistant_text = (
                    "Something unexpected happened 🍉. "
                    "Please try again."
                )
        
        # AIbot response
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
        with st.chat_message("assistant"):
            st.markdown(assistant_text)
