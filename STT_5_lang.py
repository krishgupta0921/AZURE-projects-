import streamlit as st

st.title("🚀 Streamlit Connection Test")

st.write("If you can see this, your VS Code is successfully running the app!")

# Step 1: Check UI Interaction
name = st.text_input("What is your name?")
if name:
    st.success(f"Hello {name}! The UI is working perfectly.")

# Step 2: Check Layout Components
st.subheader("Feature Test")
col1, col2 = st.columns(2)

with col1:
    if st.button("Click Me"):
        st.balloons()
        st.write("Button works!")

with col2:
    lang = st.selectbox("Select a test language", ["English", "French", "Spanish"])
    st.write(f"You selected: {lang}")

st.divider()
st.info("Next Step: Paste your Azure Speech code into this file to test the AI features.")