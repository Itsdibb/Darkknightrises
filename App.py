import streamlit as st


st.title("Authenticate")

if not st.experimental_user.is_logged_in:
    if st.button("Log in"):
        st.login()

st.json(st.experimental_user)

