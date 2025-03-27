import streamlit as st


st.title("Authenticate")

if not st.experimental_user.is_logged_in:
    if st.button("Log in"):
        st.login("auth0")

st.json(st.experimental_user)

