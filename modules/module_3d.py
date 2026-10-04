import streamlit as st
import trimesh
import numpy as np
import tempfile
import os
from google import genai
import plotly.graph_objects as go

from src.slice_analysis import extract_2d_profile_from_mesh, calculate_v_angle, create_mock_v_groove_mesh
from src.translations import TRANSLATIONS

def run():
    # --- Language Selection ---
    lang_choice = st.sidebar.selectbox("Language / Språk", ["Svenska", "English"], key="lang_choice")
    lang = "sv" if lang_choice == "Svenska" else "en"
    t = TRANSLATIONS[lang]

    # --- Initialize Session State ---
    if 'cut_a' not in st.session_state:
        st.session_state['cut_a'] = None
    if 'cut_b' not in st.session_state:
        st.session_state['cut_b'] = None

    st.title(t["title"])
    st.markdown(t["subtitle"])

    # --- Sidebar ---
    st.sidebar.header(t["sidebar_upload"])
    gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password", placeholder=t["api_key_placeholder"])
    st.sidebar.markdown("---")
    uploaded_file = st.sidebar.file_uploader(t["upload_file"], type=['stl', 'obj'])
    use_mock = st.sidebar.checkbox(t["use_mock"], value=(uploaded_file is None))

    st.sidebar.subheader(t["sidebar_settings"])
    plane_origin_x = st.sidebar.number_input("Origin X", value=0.0)
    plane_origin_y = st.sidebar.number_input("Origin Y", value=0.0)
    plane_origin_z = st.sidebar.number_input("Origin Z", value=0.0)

    dir_x = st.sidebar.number_input("Direction X", value=0.0)
    dir_y = st.sidebar.number_input("Direction Y", value=1.0)
    dir_z = st.sidebar.number_input("Direction Z", value=0.0)

    up_x = st.sidebar.number_input("Up Vector X", value=0.0)
    up_y = st.sidebar.number_input("Up Vector Y", value=0.0)
    up_z = st.sidebar.number_input("Up Vector Z", value=1.0)

    st.sidebar.markdown("---")
    st.sidebar.subheader(t["sidebar_metadata"])
    st.sidebar.markdown(t["meta_desc"])
    meta_stone = st.sidebar.selectbox(t["stone_type"], t["options_stone"])
    meta_weathering = st.sidebar.selectbox(t["weathering"], t["options_weathering"])
    meta_region = st.sidebar.selectbox(t["region"], t["options_region"])
    meta_period = st.sidebar.selectbox(t["period"], t["options_period"])

    tab1, tab2 = st.tabs([t["tab_analysis"], t["tab_ai"]])

    with tab1:
        st.subheader(t["analysis_header"])
        st.markdown(t["analysis_desc"])
        if st.button(t["btn_analyze"], type="primary"):
            with st.spinner(t["loading"]):
                mesh = None
                if use_mock:
                    mesh = create_mock_v_groove_mesh()
                elif uploaded_file is not None:
                    with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split('.')[-1]) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    try:
                        mesh = trimesh.load(tmp_path)
                    except Exception as e:
                        st.error(f"{t['error_load']} {e}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                
                if mesh is not None:
                    plane_origin = [plane_origin_x, plane_origin_y, plane_origin_z]
                    groove_direction = [dir_x, dir_y, dir_z]
                    up_vector = [up_x, up_y, up_z]
                    
                    try:
                        x_2d, z_2d = extract_2d_profile_from_mesh(mesh, plane_origin, groove_direction, up_vector)
                        if use_mock:
                            z_2d += np.random.normal(0, 0.1, size=z_2d.shape)
                        
                        results = calculate_v_angle(x_2d, z_2d)
                        st.session_state['current_results'] = results
                        st.session_state['current_plot'] = (x_2d, z_2d, results)
                    except Exception as e:
                        st.error(f"{t['error_analysis']} {e}")

        # Visa senaste resultatet
        if 'current_results' in st.session_state:
            st.markdown("---")
            results = st.session_state['current_results']
            
            c1, c2, c3 = st.columns(3)
            c1.metric(t["v_angle"], f"{results['apex_vinkel_deg']:.2f}°")
            c2.metric(t["asymmetry"], f"{results['asymmetri_deg']:.2f}°")
            c3.metric(t["depth"], f"{results['spårdjup_mm']:.2f} mm")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            x_2d, z_2d, _ = st.session_state['current_plot']
            apex_idx = results["apex_idx"]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x_2d, y=z_2d, 
                mode='markers', 
                name='Data',
                marker=dict(color='#2d3748', size=5),
                hovertemplate='X: %{x:.2f} mm<br>Z: %{y:.2f} mm<extra></extra>'
            ))
            
            # The user changed slice_analysis.py to include shoulders!
            left_shoulder = results.get("left_shoulder", 0)
            right_shoulder = results.get("right_shoulder", len(x_2d)-1)
            
            x_left, x_right = x_2d[left_shoulder:apex_idx], x_2d[apex_idx+1:right_shoulder]
            
            if len(x_left) > 0 and len(x_right) > 0:
                k1, m1 = results["fit_left"]
                k2, m2 = results["fit_right"]
                
                fig.add_trace(go.Scatter(x=x_left, y=k1 * x_left + m1, mode='lines', name='Left/Vänster', line=dict(color='#e53e3e', width=3)))
                fig.add_trace(go.Scatter(x=x_right, y=k2 * x_right + m2, mode='lines', name='Right/Höger', line=dict(color='#3182ce', width=3)))
            
            fig.update_layout(
                title=t["plot_title"],
                xaxis_title='X (mm)',
                yaxis_title='Z (mm)',
                yaxis=dict(scaleanchor="x", scaleratio=1),
                hovermode='closest',
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"#### {t['save_header']}")
            sc1, sc2 = st.columns(2)
            
            # Spara nuvarande mätvärden OCH sidopanelens metadata
            save_data = results.copy()
            save_data['metadata'] = {
                'stenart': meta_stone,
                'vittring': meta_weathering,
                'region': meta_region,
                'period': meta_period
            }
            
            if sc1.button(t["btn_save_a"], use_container_width=True):
                st.session_state['cut_a'] = save_data
                st.success(t["saved_a"])
            if sc2.button(t["btn_save_b"], use_container_width=True):
                st.session_state['cut_b'] = save_data
                st.success(t["saved_b"])

    with tab2:
        st.subheader(t["ai_header"])
        st.markdown(t["ai_desc"])
        
        st.markdown(f"##### {t['your_data']}")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{t['cut_a']}**")
            if st.session_state['cut_a'] is not None:
                a = st.session_state['cut_a']
                st.info(f"**{t['geom']}:** {t['v_angle']}: {a['apex_vinkel_deg']:.1f}° | {t['depth']}: {a['spårdjup_mm']:.2f}mm | {t['asymmetry']}: {a['asymmetri_deg']:.1f}°\n\n**{t['ctx']}:** {a['metadata']['stenart']} | {a['metadata']['vittring']} | {a['metadata']['period']} | {a['metadata']['region']}")
            else:
                st.warning(t["missing"])
                
        with c2:
            st.markdown(f"**{t['cut_b']}**")
            if st.session_state['cut_b'] is not None:
                b = st.session_state['cut_b']
                st.info(f"**{t['geom']}:** {t['v_angle']}: {b['apex_vinkel_deg']:.1f}° | {t['depth']}: {b['spårdjup_mm']:.2f}mm | {t['asymmetry']}: {b['asymmetri_deg']:.1f}°\n\n**{t['ctx']}:** {b['metadata']['stenart']} | {b['metadata']['vittring']} | {b['metadata']['period']} | {b['metadata']['region']}")
            else:
                st.warning(t["missing"])

        st.markdown("---")

        if st.session_state['cut_a'] is not None and st.session_state['cut_b'] is not None:
            if st.button(t["btn_ai"], type="primary", use_container_width=True):
                if not gemini_api_key:
                    st.error(t["error_no_api"])
                else:
                    with st.spinner(t["waiting_ai"]):
                        try:
                            client = genai.Client(api_key=gemini_api_key)
                            a = st.session_state['cut_a']
                            b = st.session_state['cut_b']
                            
                            prompt = f"""
{t['prompt_role']}
{t['prompt_task']}

{t['prompt_context']}

{t['prompt_a']}
- {t['geom']}: {a['apex_vinkel_deg']:.2f}° | {a['asymmetri_deg']:.2f}° | {a['spårdjup_mm']:.2f} mm
- {t['ctx']}: {a['metadata']['stenart']} | {a['metadata']['vittring']} | {a['metadata']['period']} | {a['metadata']['region']}

{t['prompt_b']}
- {t['geom']}: {b['apex_vinkel_deg']:.2f}° | {b['asymmetri_deg']:.2f}° | {b['spårdjup_mm']:.2f} mm
- {t['ctx']}: {b['metadata']['stenart']} | {b['metadata']['vittring']} | {b['metadata']['period']} | {b['metadata']['region']}

{t['prompt_end']}
                            """
                            response = client.models.generate_content(
                                model='gemini-pro-latest',
                                contents=prompt,
                            )
                            st.markdown(f"### {t['ai_result']}")
                            st.markdown(response.text)
                        except Exception as e:
                            st.error(f"{t['error_ai']} {e}")
