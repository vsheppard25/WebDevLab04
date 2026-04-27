import streamlit as st
import requests
import pandas as pd
from google import genai

st.set_page_config(page_title="Fruit Data Chatbot", page_icon="🍇")

st.title("🍇 Fruit Data Chatbot")
st.write(
    "Ask questions about fruit nutrition. This chatbot uses live Fruityvice API data "
    "as context for Gemini."
)

@st.cache_data
def fetch_all_fruits():
    response = requests.get("https://www.fruityvice.com/api/fruit/all", timeout=10)
    response.raise_for_status()
    data = response.json()

    rows = []
    for fruit in data:
        nutrition = fruit.get("nutritions", {})
        rows.append({
            "Name": fruit.get("name", "Unknown"),
            "Family": fruit.get("family", "Unknown"),
            "Calories": nutrition.get("calories", 0),
            "Fat": nutrition.get("fat", 0),
            "Sugar": nutrition.get("sugar", 0),
            "Carbohydrates": nutrition.get("carbohydrates", 0),
            "Protein": nutrition.get("protein", 0),
        })

    return pd.DataFrame(rows).sort_values("Name").reset_index(drop=True)

try:
    df = fetch_all_fruits()
except Exception as e:
    st.error(f"Could not fetch data from Fruityvice: {e}")
    st.stop()

fruit_names = sorted(df["Name"].tolist())

st.sidebar.header("Fruit Data Context")

selected_fruits = st.sidebar.multiselect(
    "Choose fruits the chatbot should know about",
    fruit_names,
    default=[fruit for fruit in ["Apple", "Banana", "Mango"] if fruit in fruit_names]
)

focus_goal = st.sidebar.selectbox(
    "Conversation focus",
    [
        "General nutrition advice",
        "Breakfast choice",
        "Low sugar snacks",
        "High energy snacks",
        "Smoothie ideas",
    ]
)

if selected_fruits:
    context_df = df[df["Name"].isin(selected_fruits)]
else:
    context_df = df.head(10)

st.subheader("Fruityvice Data Being Sent to Gemini")
st.dataframe(context_df, use_container_width=True)

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("Missing Gemini API key. Add GEMINI_API_KEY to .streamlit/secrets.toml.")
    st.stop()

if "fruit_chat_messages" not in st.session_state:
    st.session_state.fruit_chat_messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! Ask me about the selected fruits, their nutrition, "
                "or what fruit might fit your snack or breakfast plan."
            )
        }
    ]

for message in st.session_state.fruit_chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_prompt = st.chat_input("Ask about the selected fruit data...")

if user_prompt:
    st.session_state.fruit_chat_messages.append({
        "role": "user",
        "content": user_prompt
    })

    with st.chat_message("user"):
        st.markdown(user_prompt)

    try:
        @st.cache_resource
        def get_gemini_client():
            return genai.Client(api_key=api_key)
        client = get_gemini_client()

        fruit_context = context_df.to_string(index=False)

        conversation_history = ""
        for msg in st.session_state.fruit_chat_messages[-8:]:
            conversation_history += f"{msg['role'].upper()}: {msg['content']}\n"

        gemini_prompt = f"""
        You are a helpful fruit nutrition chatbot.

        Use the Fruityvice API data below as your main source of truth.
        The data is per 100g of fruit.

        Conversation focus: {focus_goal}

        Fruityvice API data:
        {fruit_context}

        Recent conversation:
        {conversation_history}

        User's newest question:
        {user_prompt}

        Rules:
        - Answer using the provided fruit API data.
        - If the user asks about a fruit not shown, say it is not currently in the selected data.
        - Keep the answer conversational and useful.
        - Do not give medical advice.
        - Keep it school-appropriate.
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=gemini_prompt
        )

        assistant_text = response.text.strip() if response.text else (
            "I could not generate a fruit answer for that. Try asking another way."
        )

    except Exception as e:
        error_text = str(e).lower()

        if "rate" in error_text or "quota" in error_text or "429" in error_text:
            assistant_text = (
                "Gemini is getting too many requests right now. "
                "Please wait a moment and try again."
            )
        elif "safety" in error_text or "blocked" in error_text:
            assistant_text = (
                "Gemini blocked that response for safety reasons. "
                "Please rephrase your fruit question."
            )
        elif "api key" in error_text or "permission" in error_text or "403" in error_text:
            assistant_text = (
                "There is a Gemini API key or permission problem. "
                "Check that your GEMINI_API_KEY in Streamlit secrets is valid."
            )
        else:
            assistant_text = (
                "Something went wrong with Gemini, but the app did not crash. "
                "Please try again."
            )

    st.session_state.fruit_chat_messages.append({
        "role": "assistant",
        "content": assistant_text
    })

    with st.chat_message("assistant"):
        st.markdown(assistant_text)
