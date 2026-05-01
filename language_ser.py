import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

st.set_page_config(page_title="Azure Text Summarizer", page_icon="🧠")

# 🎯 Title
st.title("📰 Azure News Article Text Summarizer")

# 🔐 Sidebar for credentials
st.sidebar.header("🔑 Azure Credentials")

endpoint = st.sidebar.text_input("Azure Endpoint")
key = st.sidebar.text_input("Azure Key", type="password")

st.sidebar.markdown("ℹ️ Paste your Azure Language resource details")

# 📝 Text input
text = st.text_area("Enter your text here", height=200)

summary_type = st.radio(
    "Choose Summary Type",
    ["Extractive", "Abstractive"]
)

sentence_count = st.slider(
    "Number of sentences (Extractive only)",
    1, 5, 3
)

# 🚀 Button
if st.button("Generate Summary"):

    if not endpoint or not key:
        st.error("⚠️ Please enter Azure credentials in the sidebar")
        st.stop()

    if text.strip() == "":
        st.warning("⚠️ Please enter some text to summarize")
        st.stop()

    try:
        with st.spinner("Connecting to Azure..."):

            credential = AzureKeyCredential(key)
            client = TextAnalyticsClient(endpoint=endpoint, credential=credential)

            if summary_type == "Extractive":
                poller = client.begin_extract_summary(
                    [text],
                    max_sentence_count=sentence_count
                )
            else:
                poller = client.begin_abstract_summary([text])

            result = poller.result()

            for doc in result:
                if not doc.is_error:

                    st.subheader("📌 Summary")

                    if summary_type == "Extractive":
                        for sentence in doc.sentences:
                            st.write("•", sentence.text)
                    else:
                        st.write(doc.summaries[0].text)

                else:
                    st.error(doc.error)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")