import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import azure.cognitiveservices.speech.audio as speech_audio
import azure.cognitiveservices.speech.translation as speech_translation
import time

# --- UI Configuration ---
st.set_page_config(page_title="Azure Speech Master", page_icon="🎙️", layout="wide")

st.title("🎙️ Azure Speech Services Integrator")
st.markdown("A simple UI/UX for Speech-to-Text, TTS, Translation, and Speaker Recognition.")

# --- Sidebar: Configuration ---
st.sidebar.header("🔑 Azure Configuration")
st.sidebar.info("Get these from your Azure Portal > Speech Service > Keys & Endpoint.")

SPEECH_KEY = st.sidebar.text_input("Speech Key", type="password")
SPEECH_REGION = st.sidebar.text_input("Service Region", value="eastus")

if not SPEECH_KEY or not SPEECH_REGION:
    st.warning("⚠️ Please enter your Azure Speech Key and Region in the sidebar to proceed.")
    st.stop()

# --- Helper Functions ---

def get_speech_config():
    config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    return config

def recognize_speech():
    speech_config = get_speech_config()
    speech_config.speech_recognition_language = "en-US"
    audio_config = speech_audio.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    status_text.text("Listening...")
    result = recognizer.recognize_once_async().get()
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return "No speech recognized."
    elif result.reason == speechsdk.ResultReason.Canceled:
        return f"Canceled: {result.cancellation_details.reason}"
    return "Unknown error"

def synthesize_speech(text, voice_name="en-US-AvaMultilingualNeural"):
    speech_config = get_speech_config()
    speech_config.speech_synthesis_voice_name = voice_name
    audio_config = speech_audio.AudioConfig(use_default_microphone=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    status_text.text("Synthesizing...")
    synthesizer.speak_text_async(text).get()
    status_text.text("Done.")

def translate_speech(target_languages):
    # Translation configuration
    translation_config = speech_translation.SpeechTranslationConfig(
        subscription=SPEECH_KEY, region=SPEECH_REGION)
    
    translation_config.speech_recognition_language = "en-US"
    
    for lang in target_languages:
        translation_config.add_target_language(lang)

    audio_config = speech_audio.AudioConfig(use_default_microphone=True)
    recognizer = speech_translation.TranslationRecognizer(
        translation_config=translation_config, audio_config=audio_config)

    status_text.text("Listening & Translating...")
    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.TranslatedSpeech:
        return {
            "original": result.text,
            "translations": result.translations
        }
    else:
        return None

# --- Main UI Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🗣️ Speech to Text", 
    "🔈 Text to Speech", 
    "🌐 Translation", 
    "🆔 Speaker ID"
])

status_text = st.empty()

# === TAB 1: Speech to Text ===
with tab1:
    st.header("Speech to Text")
    st.write("Click the button and speak into your microphone.")
    if st.button("Start Recording", key="stt_btn"):
        text = recognize_speech()
        st.success(f"**Recognized:** {text}")

# === TAB 2: Text to Speech ===
with tab2:
    st.header("Text to Speech")
    text_input = st.text_area("Enter text to speak:", "Hello! This is a test of Azure Neural Voice.")
    # Simple list of neural voices
    voice_options = {
        "American (Female)": "en-US-AvaMultilingualNeural",
        "American (Male)": "en-US-AndrewMultilingualNeural",
        "British (Female)": "en-GB-SoniaNeural",
        "French (Female)": "fr-FR-DeniseNeural"
    }
    selected_voice = st.selectbox("Select Voice", list(voice_options.keys()))
    
    if st.button("Speak Text", key="tts_btn"):
        synthesize_speech(text_input, voice_options[selected_voice])
        st.success("Audio played.")

# === TAB 3: Translation ===
with tab3:
    st.header("Real-time Translation")
    st.write("Speak in English, and it will be translated.")
    
    # Dictionary of target languages (Code: Name)
    lang_options = {
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "it": "Italian",
        "ja": "Japanese"
    }
    
    selected_langs = st.multiselect(
        "Select target languages (Max 5)", 
        list(lang_options.keys()), 
        format_func=lambda x: lang_options[x],
        default=["fr", "es"]
    )
    
    if st.button("Record & Translate", key="trans_btn"):
        if not selected_langs:
            st.error("Please select at least one language.")
        else:
            result = translate_speech(selected_langs)
            if result:
                st.markdown(f"**Original:** {result['original']}")
                st.divider()
                for code, text in result['translations'].items():
                    st.markdown(f"**{lang_options[code]}:** {text}")
            else:
                st.error("Could not recognize or translate speech.")

# === TAB 4: Speaker Recognition ===
with tab4:
    st.header("Speaker Recognition")
    st.info("Note: Speaker Recognition requires a 'Standard' tier Speech resource.")
    
    # Managing State for Speaker ID
    if 'profile_id' not in st.session_state:
        st.session_state.profile_id = None

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Enrollment")
        st.write("First, create a voice profile and train it.")
        if st.button("Create & Enroll Profile"):
            try:
                # 1. Create Client
                vp_client = speechsdk.VoiceProfileClient(
                    speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
                )
                # 2. Create Profile
                profile = vp_client.create_profile_async(
                    speechsdk.VoiceProfileType.TextIndependentIdentification, "en-US"
                ).get()
                st.session_state.profile_id = profile.profile_id
                st.write(f"Profile Created: `{profile.profile_id}`")
                
                # 3. Enroll (Requires ~30s of audio ideally, we'll do a short burst for demo)
                status_text.text("Enrolling... Speak for 5-10 seconds...")
                audio_config = speech_audio.AudioConfig(use_default_microphone=True)
                enrollment_result = vp_client.enroll_profile_async(profile, audio_config).get()
                
                if enrollment_result.reason == speechsdk.ResultReason.EnrolledVoiceProfile:
                    st.success("User Enrolled Successfully!")
                else:
                    st.warning(f"Enrollment Status: {enrollment_result.reason}")
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        st.subheader("2. Identification")
        st.write("Identify if the speaker matches the profile.")
        
        # Input for Profile ID (auto-filled if created in session)
        target_profile_id = st.text_input("Profile ID to Identify", value=st.session_state.profile_id if st.session_state.profile_id else "")
        
        if st.button("Identify Speaker"):
            if not target_profile_id:
                st.error("We need a Profile ID to check against.")
            else:
                try:
                    # Setup Identification
                    config = get_speech_config()
                    audio_config = speech_audio.AudioConfig(use_default_microphone=True)
                    speaker_recognizer = speechsdk.SpeakerRecognizer(
                        speech_config=config, audio_config=audio_config)
                    
                    # Create voice profile object from ID string
                    voice_profile = speechsdk.VoiceProfile(target_profile_id, speechsdk.VoiceProfileType.TextIndependentIdentification)
                    model = speechsdk.SpeakerIdentificationModel.from_profiles([voice_profile])
                    
                    status_text.text("Listening to Identify...")
                    result = speaker_recognizer.recognize_once_async(model).get()
                    
                    if result.reason == speechsdk.ResultReason.RecognizedSpeaker:
                        st.success(f"✅ Speaker Identified! Profile ID: {result.profile_id}")
                    else:
                        st.error("❌ Speaker not identified or unknown.")
                except Exception as e:
                    st.error(f"Identification failed: {e}")