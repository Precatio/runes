import streamlit as st
from google import genai
from google.genai import types
import os

def init_chat_session():
    # Initialize the chat session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
        # Initial greeting from the AI
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hej! Jag är din seniora AI-runolog. Jag granskar data objektivt och baserar mina analyser på modern vetenskap (t.ex. 3D-skanning, huggspårsanalys och GIS). Vad vill du utforska idag?"
        })

def run():
    st.title("💬 AI Runolog (Chatt)")
    st.markdown("Diskutera runstensdata, hypotetiska samband och analysresultat med en AI tränad att agera som en modern, vetenskaplig runolog.")
    
    # Hämta API-nyckel
    st.sidebar.markdown("---")
    st.sidebar.subheader("API-Konfiguration")
    
    default_key = ""
    if "GEMINI_API_KEY" in st.secrets:
        default_key = st.secrets["GEMINI_API_KEY"]
    elif "GEMINI_API_KEY" in os.environ:
        default_key = os.environ["GEMINI_API_KEY"]
        
    api_key_input = st.sidebar.text_input("Gemini API Key", type="password", value=default_key)
    
    if not api_key_input:
        st.error("Vänligen ange din Gemini API-nyckel i menyn till vänster för att chatta med AI:n.")
        return

    client = genai.Client(api_key=api_key_input)

    # Definiera systemprompten för att sätta AI:ns persona
    system_instruction = """
Du är en senior och djupt kunnig runolog. Du baserar dina analyser på modern vetenskap, såsom huggspårsanalys, 3D-fotogrammetri och GIS, men du har även expertis inom filologi och historisk kontext.
Din roll är att granska data och användarens frågor objektivt för att hitta okända samband, utan att bli onödigt färgad av föråldrade tolkningar. 
Var direkt, vetenskaplig, analytisk och ifrågasättande.
Du svarar alltid på svenska om inte användaren ber om något annat.
Undvik onödigt långa introduktioner – gå rakt på sak i dina analyser.
"""

    init_chat_session()

    # Visa tidigare meddelanden
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Hantera ny inmatning från användaren
    if prompt := st.chat_input("Skriv din fråga eller fundering här..."):
        # Lägg till användarens meddelande i gränssnittet
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Bygg upp historiken för att skicka till Gemini (exkluderar systemprompt som hanteras separat, samt första hälsningen som ibland kan störa context, men vi skickar hela historiken som User/Model)
        contents = []
        for msg in st.session_state.messages[1:]: # Skickar inte den hårdkodade hälsningen till API:et för att undvika format-fel
            role = "USER" if msg["role"] == "user" else "MODEL"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )
            
        # Visa laddningsindikator medan AI:n tänker
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Tänker...")
            
            try:
                response = client.models.generate_content(
                    model='gemini-flash-latest',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.4, 
                    )
                )
                
                # Visa det riktiga svaret
                full_response = response.text
                message_placeholder.markdown(full_response)
                
                # Spara AI:ns svar i historiken
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                message_placeholder.error(f"Ett fel uppstod vid kommunikation med AI:n: {e}")
