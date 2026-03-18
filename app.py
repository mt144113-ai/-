import streamlit as st
import requests
import PyPDF2
import json

# إعدادات الصفحة
st.set_page_config(page_title="مساعد فرع رشيد الذكي", page_icon="💊", layout="wide")

# تنسيق الواجهة للغة العربية
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    div[data-testid="stSidebar"] { direction: rtl; }
    .stChatInput { direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد فرع رشيد - الاستعلام الذكي")

# جلب المفتاح من Secrets
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("⚠️ خطأ: لم يتم ضبط GOOGLE_API_KEY في إعدادات Secrets.")
    st.stop()

# دالة استخراج النص
def extract_text(files):
    combined_text = ""
    for f in files:
        try:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                combined_text += page.extract_text() or ""
        except Exception as e:
            st.error(f"خطأ في قراءة {f.name}: {e}")
    return combined_text

# القائمة الجانبية
with st.sidebar:
    st.header("📂 ملفات الفرع")
    uploaded_files = st.file_uploader("ارفع ملفات PDF هنا", type="pdf", accept_multiple_files=True)

# منطقة الدردشة
if uploaded_files:
    # تخزين النص في الجلسة لسرعة الاستجابة
    if 'context' not in st.session_state:
        with st.spinner("جاري تحليل الملفات..."):
            st.session_state.context = extract_text(uploaded_files)

    user_query = st.chat_input("اسأل سؤالاً عن الملفات المرفوعة...")

    if user_query:
        with st.chat_message("user"):
            st.write(user_query)

        with st.chat_message("assistant"):
            with st.spinner("جاري استخراج الإجابة..."):
                url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
                payload = {
                    "contents": [{
                        "parts": [{"text": f"أجب باللغة العربية بناءً على النص التالي فقط:\n{st.session_state.context}\n\nالسؤال: {user_query}"}]
                    }]
                }
                try:
                    response = requests.post(url, json=payload, timeout=30)
                    if response.status_code == 200:
                        answer = response.json()['candidates'][0]['content']['parts'][0]['text']
                        st.write(answer)
                    elif response.status_code == 429:
                        st.error("⚠️ ضغط طلبات كبير، حاول مجدداً بعد دقيقة.")
                    else:
                        st.error(f"خطأ {response.status_code}")
                except Exception as e:
                    st.error(f"فشل الاتصال: {e}")
else:
    st.info("👈 من فضلك ارفع ملف PDF للبدء.")
