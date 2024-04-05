import streamlit as st

import os

language_emoji_map = {
    'Spanish': '🇪🇸', 'English': '🇬🇧', 'Portuguese': '🇵🇹',
    'Polish': '🇵🇱', 'Russian': '🇷🇺', 'French': '🇫🇷',
    'German': '🇩🇪', 'Italian': '🇮🇹'
}


def scan_documents(directory='generated_documents'):
    documents = {lang: [] for lang in language_emoji_map.keys()}
    for file in os.listdir(directory):
        if file.endswith(".pdf"):
            for lang in language_emoji_map.keys():
                if f"_{lang}_" in file:
                    documents[lang].append(file)
                    break
    return documents


# Initialize or refresh the document list in session state
if 'documents' not in st.session_state or st.sidebar.button('Refresh Document List 🔄'):
    st.session_state.documents = scan_documents()

# Display download buttons for each document
for lang, docs in st.session_state.documents.items():
    st.sidebar.write(f"{language_emoji_map.get(lang, '')} {lang} Documents")
    for doc in docs:
        with open(f"generated_documents/{doc}", "rb") as file:
            st.sidebar.download_button(
                label=f"Download {os.path.splitext(doc)[0]}",
                data=file,
                file_name=doc,
                mime="application/octet-stream"
            )
