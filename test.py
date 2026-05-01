import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.translation.text import TextTranslationClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import time
import json

st.set_page_config(page_title="Perception Intelligence System", layout="wide")

st.title("🧠 Distributed Perception Intelligence System")

# ---------------- SIDEBAR ----------------
st.sidebar.header("🔑 Azure Credentials")

doc_endpoint = st.sidebar.text_input("Document Intelligence Endpoint")
doc_key = st.sidebar.text_input("Document Intelligence Key", type="password")

vision_endpoint = st.sidebar.text_input("Vision Endpoint")
vision_key = st.sidebar.text_input("Vision Key", type="password")

lang_endpoint = st.sidebar.text_input("Language Endpoint")
lang_key = st.sidebar.text_input("Language Key", type="password")

trans_endpoint = st.sidebar.text_input("Translator Endpoint")
trans_key = st.sidebar.text_input("Translator Key", type="password")

# ---------------- INPUT MODE ----------------
st.header("📥 Input Options")

input_mode = st.radio("Choose Input Type:", ["Upload File", "Enter Text"])

text = ""

# ---------------- FUNCTIONS ----------------

def extract_text_document_intelligence(file_bytes):
    client = DocumentAnalysisClient(
        endpoint=doc_endpoint,
        credential=AzureKeyCredential(doc_key)
    )
    poller = client.begin_analyze_document("prebuilt-read", file_bytes)
    result = poller.result()

    text = ""
    for page in result.pages:
        for line in page.lines:
            text += line.content + "\n"
    return text


def extract_text_vision(file_bytes):
    client = ComputerVisionClient(
        vision_endpoint,
        CognitiveServicesCredentials(vision_key)
    )

    result = client.read_in_stream(file_bytes, raw=True)
    operation_id = result.headers["Operation-Location"].split("/")[-1]

    while True:
        read_result = client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    text = ""
    if read_result.status.lower() == "succeeded":
        for page in read_result.analyze_result.read_results:
            for line in page.lines:
                text += line.text + "\n"
    return text


def translate_text(text):
    try:
        client = TextTranslationClient(
            endpoint=trans_endpoint,
            credential=AzureKeyCredential(trans_key)
        )

        response = client.translate(
            body=[{"text": text}],
            to_language=["en"]
        )

        return response[0].translations[0].text

    except Exception as e:
        return f"[Translation Error] {e}"


def analyze_text(text):
    client = TextAnalyticsClient(
        endpoint=lang_endpoint,
        credential=AzureKeyCredential(lang_key)
    )

    sentiment_result = client.analyze_sentiment([text])[0]
    key_phrase_result = client.extract_key_phrases([text])[0]

    return {
        "sentiment": sentiment_result.sentiment,
        "confidence_scores": {
            "positive": sentiment_result.confidence_scores.positive,
            "neutral": sentiment_result.confidence_scores.neutral,
            "negative": sentiment_result.confidence_scores.negative
        },
        "key_phrases": key_phrase_result.key_phrases
    }


# ---------------- FILE INPUT ----------------
if input_mode == "Upload File":
    uploaded_file = st.file_uploader("Upload Image or PDF", type=["png", "jpg", "jpeg", "pdf"])

    ocr_method = st.selectbox("Choose OCR Method", ["Document Intelligence", "Computer Vision"])

    if uploaded_file:
        file_bytes = uploaded_file.read()

        st.subheader("📄 Extracting Text...")

        try:
            if ocr_method == "Document Intelligence":
                text = extract_text_document_intelligence(file_bytes)
            else:
                text = extract_text_vision(file_bytes)

        except Exception as e:
            st.error(f"OCR Error: {e}")


# ---------------- TEXT INPUT ----------------
elif input_mode == "Enter Text":
    text = st.text_area("Enter your text here:", height=200)


# ---------------- OPTIONS ----------------
st.header("⚙️ Processing Options")
translate_option = st.checkbox("Translate to English")

# ---------------- RUN ----------------
if st.button("🚀 Run Analysis"):

    if not text.strip():
        st.warning("Please provide input text or upload a file.")
    else:
        st.subheader("📝 Original Text")
        st.text_area("Text", text, height=150)

        # Translation
        if translate_option:
            st.subheader("🌐 Translating...")
            text = translate_text(text)
            st.text_area("Translated Text", text, height=150)

        # Analysis
        try:
            st.subheader("🔍 Analyzing Text...")
            analysis = analyze_text(text)

            st.json(analysis)

            structured_output = {
                "input_text": text[:500],
                "analysis": analysis
            }

            st.subheader("📦 Structured Output (JSON)")
            st.code(json.dumps(structured_output, indent=2), language="json")

        except Exception as e:
            st.error(f"Analysis Error: {e}")