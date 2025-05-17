import streamlit as st
import pandas as pd
import joblib
import requests
import io
from datetime import datetime
from fpdf import FPDF
import base64

# GitHub model URLs
base_url = "https://raw.githubusercontent.com/RahafRsq/password-strength-checker/main/"
model_urls = {
    "logistic_regression": base_url + "logistic_regression_model.pkl",
    "random_forest": base_url + "random_forest_model.pkl",
    "knn": base_url + "knn_model.pkl",
    "svm": base_url + "svm_model.pkl",
    "label_encoder": base_url + "label_encoder.pkl"
}

@st.cache_resource
def load_model_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        st.error(f"❌ Failed to load model from: {url}")
        st.stop()
    return joblib.load(io.BytesIO(response.content))

def check_password_strength(password):
    features = {
        'Has Lowercase': int(any(c.islower() for c in password)),
        'Has Uppercase': int(any(c.isupper() for c in password)),
        'Has Special Character': int(any(not c.isalnum() for c in password)),
        'Length': len(password)
    }
    X = pd.DataFrame([features])
    label_encoder = load_model_from_url(model_urls['label_encoder'])
    models = {
        'Logistic Regression': load_model_from_url(model_urls['logistic_regression']),
        'Random Forest': load_model_from_url(model_urls['random_forest']),
        'K-Nearest Neighbors': load_model_from_url(model_urls['knn']),
        'Support Vector Machine': load_model_from_url(model_urls['svm'])
    }

    predictions = {}
    for name, model in models.items():
        try:
            pred_num = model.predict(X)[0]
            pred_label = label_encoder.inverse_transform([pred_num])[0]
            predictions[name] = pred_label
        except Exception as e:
            predictions[name] = f"Error: {e}"

    return predictions

def create_pdf(password, predictions):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Password Strength Report", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Password: {password}", ln=True)
    pdf.cell(0, 10, f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(5)

    for model, result in predictions.items():
        pdf.cell(0, 10, f"{model}: {result}", ln=True)

    # ✅ FIX: return binary content
    return pdf.output(dest="S").encode("latin1")

# === UI ===
st.title("🔐 Password Strength Checker")

# Responsive + dark style
st.markdown("""
    <style>
    @media (max-width: 600px) {
        div[data-testid="column"] {
            width: 100% !important;
            display: block;
        }
        .css-1v3fvcr {
            flex-direction: column !important;
        }
    }
    body {
        background-color: #0e1117;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

if 'show_password' not in st.session_state:
    st.session_state.show_password = False

def toggle_visibility():
    st.session_state.show_password = not st.session_state.show_password

col_eye, col_input = st.columns([0.1, 0.9])
with col_eye:
    if st.button("👁️"):
        toggle_visibility()
with col_input:
    st.write("")

password = st.text_input("Enter your password:", type="default" if st.session_state.show_password else "password")

if password:
    if len(password) < 6:
        st.warning("⚠️ Your password is very short. Use at least 6 characters.")

    length = len(password)
    if length >= 13:
        strength_info = ("Strong", "Strong password", "green", "🟢")
    elif length >= 9:
        strength_info = ("Medium", "Moderate password", "orange", "🟡")
    else:
        strength_info = ("Weak", "Weak password", "red", "🔴")

    st.subheader("📊 Length-Based Strength Estimate")
    st.markdown(
        f"<div style='padding:10px; border-radius:10px; background-color:{strength_info[2]}; color:white; font-size:18px;'>"
        f"{strength_info[3]} <strong>{strength_info[0]}</strong> — {strength_info[1]}"
        f"</div>",
        unsafe_allow_html=True
    )

    st.subheader("🤖 Model Predictions:")
    predictions = check_password_strength(password)

    style_map = {
        'Weak': {'color': 'red', 'emoji': '🔴', 'description': 'Weak password'},
        'Medium': {'color': 'orange', 'emoji': '🟡', 'description': 'Moderate password'},
        'Strong': {'color': 'green', 'emoji': '🟢', 'description': 'Strong password'}
    }

    for model, result in predictions.items():
        style = style_map.get(result, {'color': 'black', 'emoji': '', 'description': result})
        st.markdown(
            f"**{model}:** <span style='color:{style['color']}'>{result} {style['emoji']} - {style['description']}</span>",
            unsafe_allow_html=True
        )

    st.subheader("💡 Password Tips:")
    tips = [
        "Use a mix of lowercase and uppercase letters.",
        "Include special characters like @, #, or $.",
        "Make your password at least 12 characters.",
        "Try a memorable passphrase instead of one word."
    ]
    for tip in tips:
        st.write(f"▫️ {tip}")

    # PDF ready
    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        st.success("✅ Your password result is ready for download.")
    with col2:
        pdf_bytes = create_pdf(password, predictions)
        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(f"""
            <a href="data:application/octet-stream;base64,{b64}" download="password_result.pdf">
                <div style="
                    background-color:#1f6feb;
                    padding:13px;
                    border-radius:10px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    height: 48px;
                    width: 48px;
                    color:white;
                    font-size:22px;
                    box-shadow: 0 0 4px #00000055;
                    border:1px solid #444444;
                ">
                    ⬇️
                </div>
            </a>
        """, unsafe_allow_html=True)
