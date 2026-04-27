import streamlit as st
import requests
from google import genai

st.set_page_config(page_title="Fruit Recipe Generator", page_icon="🥤")

st.title("🥤 AI Fruit Recipe Generator")
st.write(
    "Pick some fruits and a health goal, and Gemini will generate a "
    "personalized smoothie recipe based on real nutritional data!"
)

# ── Fetch all fruits from Fruityvice API ───────────────────────────────────────
@st.cache_data
def fetch_all_fruits():
    response = requests.get("https://www.fruityvice.com/api/fruit/all", timeout=10)
    response.raise_for_status()
    data = response.json()

    fruits = {}
    for fruit in data:
        name = fruit.get("name", "Unknown")
        nutritions = fruit.get("nutritions", {})
        fruits[name] = {
            "family":        fruit.get("family", "Unknown"),
            "calories":      nutritions.get("calories", 0),
            "fat":           nutritions.get("fat", 0),
            "sugar":         nutritions.get("sugar", 0),
            "carbohydrates": nutritions.get("carbohydrates", 0),
            "protein":       nutritions.get("protein", 0),
        }
    return dict(sorted(fruits.items()))

try:
    all_fruits = fetch_all_fruits()
except Exception as e:
    st.error(f"Could not fetch fruit data from the Fruityvice API: {e}")
    st.stop()

fruit_names = list(all_fruits.keys())

# ── User Inputs ────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🍓 Step 1: Choose your fruits")

default_picks = [n for n in ["Banana", "Strawberry", "Mango"] if n in fruit_names]
selected_fruits = st.multiselect(
    "Select 2–5 fruits to include in your recipe",
    fruit_names,
    default=default_picks,
    help="These fruits' nutritional data will be sent to Gemini to generate your recipe."
)

st.subheader("🎯 Step 2: Choose a health goal")

goal = st.selectbox(
    "What is your health goal?",
    [
        "High energy boost",
        "Low sugar / diabetic-friendly",
        "High protein / post-workout",
        "Weight loss / low calorie",
        "Digestive health",
        "General healthy snack",
    ]
)

st.subheader("🥛 Step 3: Choose a recipe type")

recipe_type = st.selectbox(
    "What kind of recipe would you like?",
    ["Smoothie", "Fruit salad", "Overnight oats with fruit", "Fruit parfait"]
)

# ── Generate button ────────────────────────────────────────────────────────────
st.markdown("---")
generate = st.button("✨ Generate My Recipe", type="primary")

if generate:
    if len(selected_fruits) < 2:
        st.warning("Please select at least 2 fruits to generate a recipe.")
    else:
        # Build a nutritional summary of selected fruits to pass into Gemini
        nutrition_summary = ""
        for fruit_name in selected_fruits:
            data = all_fruits[fruit_name]
            nutrition_summary += (
                f"\n- {fruit_name} (per 100g): "
                f"{data['calories']} kcal, "
                f"{data['carbohydrates']}g carbs, "
                f"{data['sugar']}g sugar, "
                f"{data['fat']}g fat, "
                f"{data['protein']}g protein"
            )

        prompt = f"""
You are a nutritionist and recipe creator. A user wants to make a {recipe_type.lower()} 
using the following fruits. Here is the real nutritional data for each fruit (per 100g):

{nutrition_summary}

The user's health goal is: {goal}

Based on this data and their goal, please generate:
1. A creative name for the recipe
2. The exact ingredients with quantities (use the selected fruits plus any common 
   pantry/fridge items that complement the goal)
3. Step-by-step instructions
4. A brief nutritional summary explaining why this recipe suits the user's goal, 
   referencing the actual data provided above

Keep the tone friendly and encouraging. Format your response clearly with headers 
for each section.
"""

        api_key = st.secrets.get("GEMINI_API_KEY", "")

        if not api_key:
            st.error("No Gemini API key found. Add GEMINI_API_KEY to your Streamlit secrets.")
        else:
            try:
                with st.spinner("Generating your personalized recipe..."):
                    @st.cache_resource
                    def get_gemini_client():
                        return genai.Client(api_key=api_key)
                    client = get_gemini_client()
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                    recipe_text = response.text.strip() if response.text else None

                if recipe_text:
                    st.success("Here's your personalized recipe!")
                    st.markdown("---")

                    # Show which fruits and goal were used
                    st.caption(
                        f"Generated for: **{', '.join(selected_fruits)}** · "
                        f"Goal: **{goal}** · Type: **{recipe_type}**"
                    )

                    st.markdown(recipe_text)

                    # Show the raw nutritional data that was fed to Gemini
                    with st.expander("📊 Nutritional data sent to Gemini"):
                        st.text(nutrition_summary.strip())
                else:
                    st.warning("Gemini returned an empty response. Please try again.")

            except Exception as e:
                error_text = str(e).lower()

                if "rate" in error_text or "quota" in error_text or "429" in error_text:
                    st.error("Too many requests at once 🍍. Please wait a moment and try again.")
                elif "api key" in error_text or "permission" in error_text or "auth" in error_text:
                    st.error("There seems to be a problem with the Gemini API key 🍊.")
                elif "safety" in error_text or "blocked" in error_text:
                    st.error("That request was blocked for safety reasons 🍒. Please try different inputs.")
                else:
                    st.error(f"Something unexpected happened 🍉: {e}")
