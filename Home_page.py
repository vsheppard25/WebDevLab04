import streamlit as st
st.set_page_config(page_title="Fruit App", page_icon="🍓")
st.title("🍓 Welcome to the Fruit App!")
st.write("Use the sidebar to navigate between pages.")
st.markdown("---")
st.header("📖 About This App")
st.write(
    "This app lets you explore the world of fruit through data and conversation. "
    "Whether you're curious about nutrition or just looking for recipe ideas, we've got you covered!"
)
st.markdown("---")
st.header("📄 Pages")
st.subheader("🍊 Fruit Nutrition Explorer")
st.write(
    "Analyze and compare the nutritional content of fruits from around the world. "
    "Filter by nutrient, compare multiple fruits side by side, and explore "
    "macronutrient breakdowns — all powered by the Fruityvice API."
)
st.subheader("🥝 Fruit Bot")
st.write(
    "Interact with a fruit chatbot to learn all about fruit, nutrition, "
    "snack ideas, or smoothie recipes 🍎🍌🍇"
)
st.subheader("🥤 Fruit Recipe Generator")
st.write(
    "Pick your favorite fruits and a health goal, and get a personalized recipe "
    "generated just for you! Powered by real nutritional data from the Fruityvice API "
    "and Gemini AI. 🍓🥭🍌"
)
st.subheader("🍇 Fruit Data Chatbot")
st.write(
    "Ask questions about fruit nutrition and get answers grounded in real data. "
    "Select specific fruits and a conversation focus, and chat with Gemini using "
    "live Fruityvice API data as context. 🍇🍍🍊"
)
