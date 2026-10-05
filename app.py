import streamlit as st
import importlib

# Måste vara första anropet
st.set_page_config(page_title="Bifrost", layout="wide", page_icon="🗿")

# --- Custom SaaS CSS ---
# Detta ger en modernare känsla med rundade hörn, glas-effekter och bättre typografi.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Mörk bakgrund med en extremt subtil gradient för djup */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #111827 100%);
    }

    /* Göm Streamlit-specifikt skräp (header, footer, deploy-knapp, top-decoration) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .st-emotion-cache-1dp5vir {background-image: none;} /* Göm top gradient line */
    
    /* Sidofältet (Sidebar) Glassmorphism */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Snygga till Navigationen (Radio buttons) så de ser ut som menyval */
    div[role="radiogroup"] > label {
        background: transparent;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 4px;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    div[role="radiogroup"] > label:hover {
        background-color: rgba(99, 102, 241, 0.1);
        transform: translateX(4px);
    }
    /* Göm själva runda radio-knappen */
    div[role="radiogroup"] div[data-testid="stMarkdownContainer"] p {
        font-size: 1.05rem;
        font-weight: 500;
        color: #e2e8f0;
    }
    div[role="radiogroup"] div[class*="st-emotion-cache"] {
        display: none !important; /* Dölj radio-cirklarna */
    }
    /* Indikation på valt objekt */
    div[role="radiogroup"] > label[data-baseweb="radio"][aria-checked="true"] {
        background: linear-gradient(90deg, rgba(99,102,241,0.2) 0%, rgba(99,102,241,0) 100%);
        border-left: 4px solid #6366f1;
    }

    /* Justerar padding för huvudinnehållet */
    .block-container {
        padding-top: 3rem !important;
        padding-left: 4rem !important;
        padding-right: 4rem !important;
        max-width: 1200px;
    }
    
    /* Headers */
    h1 {
        font-weight: 700 !important;
        font-size: 2.8rem !important;
        background: -webkit-linear-gradient(45deg, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem !important;
    }
    h2, h3 {
        font-weight: 600 !important;
        color: #f8fafc !important;
        letter-spacing: -0.025em;
    }

    /* Textfält och chatt-input */
    .stTextInput > div > div > input,
    .stChatInput > div {
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background-color: rgba(30, 41, 59, 0.5) !important;
        color: #f8fafc !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stChatInput > div:focus-within {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
    }

    /* Chattmeddelanden (Bubblor) */
    [data-testid="chatAvatarIcon-user"] {
        background-color: #3b82f6 !important;
    }
    [data-testid="chatAvatarIcon-assistant"] {
        background-color: #8b5cf6 !important;
    }
    .stChatMessage {
        background-color: transparent !important;
        padding: 0 !important;
        margin-bottom: 1.5rem !important;
    }
    .stChatMessage [data-testid="stMarkdownContainer"] {
        background-color: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255,255,255,0.05);
        padding: 16px 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        font-size: 1.05rem;
        line-height: 1.6;
        color: #e2e8f0;
    }
    
    /* Snygga till knappar */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
        border: none !important;
        box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.39) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.23) !important;
    }

</style>
""", unsafe_allow_html=True)

st.sidebar.title("Appar & Moduler")
st.sidebar.markdown("---")

module_choice = st.sidebar.radio("Navigera", [
    "🔍 3D Huggspårsanalys", 
    "🌍 Karta (GIS/GPS)", 
    "💬 AI Runolog (Chatt)",
    "📖 Lingvistisk Analys (NLP)"
])

st.sidebar.markdown("---")
st.sidebar.info("Byggt av Viktor Kvant. Optimerad för data- och runforskning.")

if module_choice == "🔍 3D Huggspårsanalys":
    from modules import module_3d
    importlib.reload(module_3d)
    module_3d.run()

elif module_choice == "🌍 Karta (GIS/GPS)":
    from modules import module_gis
    importlib.reload(module_gis)
    module_gis.run()

elif module_choice == "💬 AI Runolog (Chatt)":
    from modules import module_chat
    importlib.reload(module_chat)
    module_chat.run()

elif module_choice == "📖 Lingvistisk Analys (NLP)":
    from modules import module_nlp
    importlib.reload(module_nlp)
    module_nlp.run()
