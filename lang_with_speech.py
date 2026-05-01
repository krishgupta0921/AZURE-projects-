import streamlit as st
import requests
import uuid

from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
import azure.cognitiveservices.speech as speechsdk

# ================= UI =================
st.set_page_config(page_title="Azure AI News Summarizer", page_icon="🧠")
st.title("🧠 Azure Summarizer → 🌍 Translator → 🔊 Speech")

# ================= SIDEBAR =================
st.sidebar.header("🔑 Azure Credentials")

lang_key = st.sidebar.text_input("Language Key", type="password")
lang_endpoint = st.sidebar.text_input("Language Endpoint")

translator_key = st.sidebar.text_input("Translator Key", type="password")
translator_region = st.sidebar.text_input("Translator Region")
translator_endpoint = "https://api.cognitive.microsofttranslator.com"

speech_key = st.sidebar.text_input("Speech Key", type="password")
speech_region = st.sidebar.text_input("Speech Region")

# ================= LANGUAGE MAP =================
languages = {
    "English": ("en", "en-US-JennyNeural"),
    "Hindi": ("hi", "hi-IN-SwaraNeural"),
    "Spanish": ("es", "es-ES-ElviraNeural"),
    "French": ("fr", "fr-FR-DeniseNeural"),
    "German": ("de", "de-DE-KatjaNeural"),
}

selected_language = st.selectbox("🌍 Output Language", list(languages.keys()))

# ================= INPUT =================
text = st.text_area("📝 Enter text", height=200)

summary_type = st.radio("Summary Type", ["Abstractive", "Extractive"])

sentence_count = 3
if summary_type == "Extractive":
    sentence_count = st.slider("Extractive Sentences", 1, 5, 3)

# ================= SPEECH TEST =================
if st.sidebar.button("🔊 Test Speech Service"):

    try:
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

        result = synthesizer.speak_text_async("Speech service is working").get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            st.sidebar.success("✅ Speech service working")
        else:
            st.sidebar.error(result.cancellation_details.error_details)

    except Exception as e:
        st.sidebar.error(str(e))

# ================= MAIN BUTTON =================
if st.button("✨ Generate"):

    if not lang_key or not lang_endpoint:
        st.error("Enter Language credentials")
        st.stop()

    if not speech_key or not speech_region:
        st.error("Enter Speech credentials")
        st.stop()

    if text.strip() == "":
        st.warning("Enter text")
        st.stop()

    try:
        # ========= SUMMARIZATION =========
        with st.spinner("Summarizing..."):

            client = TextAnalyticsClient(
                endpoint=lang_endpoint,
                credential=AzureKeyCredential(lang_key)
            )

            if summary_type == "Extractive":
                poller = client.begin_extract_summary([text], max_sentence_count=sentence_count)
            else:
                poller = client.begin_abstract_summary([text])

            result = poller.result()

            summary = ""

            for doc in result:
                if doc.is_error:
                    st.error(doc.error)
                    st.stop()

                if summary_type == "Extractive":
                    summary = " ".join([s.text for s in doc.sentences])
                else:
                    summary = doc.summaries[0].text

        st.subheader("📌 Summary")
        st.write(summary)

        # ========= TRANSLATION =========
        target_lang, voice = languages[selected_language]

        if translator_key and translator_region:

            with st.spinner("Translating..."):

                url = translator_endpoint + "/translate?api-version=3.0&to=" + target_lang

                headers = {
                    "Ocp-Apim-Subscription-Key": translator_key,
                    "Ocp-Apim-Subscription-Region": translator_region,
                    "Content-type": "application/json",
                    "X-ClientTraceId": str(uuid.uuid4()),
                }

                body = [{"text": summary}]

                response = requests.post(url, headers=headers, json=body)
                response.raise_for_status()

                summary = response.json()[0]["translations"][0]["text"]

            st.subheader("🌍 Translated Text")
            st.write(summary)

        # ========= TEXT TO SPEECH (IN MEMORY) =========
        with st.spinner("Generating speech..."):

            speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=speech_region
            )

            speech_config.speech_synthesis_voice_name = voice

            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=None
            )

            result = synthesizer.speak_text_async(summary).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:

                audio_bytes = result.audio_data

                st.audio(audio_bytes, format="audio/wav")

            else:
                cancellation = result.cancellation_details
                st.error("Speech failed")
                st.write(cancellation.error_details)

        st.success("✅ Completed")

    except Exception as e:
        st.error(str(e))