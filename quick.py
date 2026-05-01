from azure.ai.vision.face import FaceClient
from azure.ai.vision.face.models import FaceDetectionModel, FaceRecognitionModel, FaceAttributeType
from azure.core.credentials import AzureKeyCredential

# --- CONFIGURATION ---
FACE_KEY = "YourFaceAPIKey"
FACE_ENDPOINT = "YourFaceAPIEndpoint"

def analyze_face_simple(image_url):
    # 1. Initialize the client
    face_client = FaceClient(FACE_ENDPOINT, AzureKeyCredential(FACE_KEY))

    # 2. Specify the attributes supported in the 2026 standard tier
    # (Emotion, Age, and Gender are now restricted/deprecated)
    features = [
        FaceAttributeType.GLASSES,
        FaceAttributeType.HEAD_POSE,
        FaceAttributeType.MASK,
        FaceAttributeType.BLUR
    ]

    print(f"Requesting analysis for URL: {image_url}")

    try:
        # 3. FIX: Use detect_from_url instead of detect for URLs
        detected_faces = face_client.detect_from_url(
            url=image_url,
            return_face_id=True,
            return_face_attributes=features,
            recognition_model=FaceRecognitionModel.RECOGNITION_04,
            detection_model=FaceDetectionModel.DETECTION03
        )

        if not detected_faces:
            print("No faces were found in the image.")
            return

        # 4. Results
        for face in detected_faces:
            print(f"\n--- Face Detected ---")
            print(f"  Face ID: {face.face_id}")
            print(f"  Glasses: {face.face_attributes.glasses}")
            print(f"  Head Pose: Yaw={face.face_attributes.head_pose.yaw}, Pitch={face.face_attributes.head_pose.pitch}")
            print(f"  Mask: {face.face_attributes.mask.type if face.face_attributes.mask else 'None'}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Ensure this URL is publicly accessible
    test_url = "https://tse3.mm.bing.net/th/id/OIP.usBx2BgFgjPmGhR24Cg-ogHaFj?rs=1&pid=ImgDetMain&o=7&rm=3"
    analyze_face_simple(test_url)