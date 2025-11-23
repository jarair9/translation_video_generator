import json
import os
import tempfile
from typing import List, Dict

import streamlit as st

from app.backgrounds import prepare_background_image
from app.cleanup import cleanup_temp
from app.video_composer import build_video
from app.gemini_script import generate_script_with_gemini


def load_example_script() -> str:
    example = [
        {"en": "I am learning Urdu", "ur": "میں اردو سیکھ رہا ہوں"},
        {"en": "This is beautiful", "ur": "یہ خوبصورت ہے"},
    ]
    return json.dumps(example, ensure_ascii=False, indent=2)


def main() -> None:
    st.set_page_config(
        page_title="Urdu-English Video Generator",
        page_icon="🎬",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .stButton>button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            padding: 0.5rem 2rem;
            font-weight: 600;
            border: none;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .css-1d391kg {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        h2, h3 {
            color: #4a5568;
            font-weight: 600;
        }
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            border-radius: 8px;
            border: 2px solid #e2e8f0;
            transition: border-color 0.3s ease;
        }
        .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
            border-color: #667eea;
        }
        .sidebar .sidebar-content {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .stDownloadButton>button {
            background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
            color: white;
            border-radius: 10px;
            padding: 0.5rem 2rem;
            font-weight: 600;
            border: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header with emoji
    st.markdown("<h1>🎬 Urdu-English Video Generator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #718096; font-size: 1.1rem; margin-bottom: 2rem;'>Create stunning bilingual videos with AI-powered script generation</p>", unsafe_allow_html=True)

    # Sidebar Configuration
    st.sidebar.markdown("### ⚙️ Settings")
    st.sidebar.markdown("---")
    
    bg_file = st.sidebar.file_uploader(
        "📸 Upload Background Image",
        type=["jpg", "jpeg", "png"],
        help="Upload a custom background for your video"
    )
    
    if bg_file:
        st.sidebar.success("✅ Background uploaded!")
    else:
        st.sidebar.info("ℹ️ No background selected - using default")
    
    st.sidebar.markdown("---")
    
    # Background Music Section
    st.sidebar.markdown("### 🎵 Background Music (Optional)")
    
    bgm_file = st.sidebar.file_uploader(
        "🎼 Upload Background Music",
        type=["mp3", "wav", "m4a"],
        help="Upload background music for your video"
    )
    
    bgm_volume = st.sidebar.slider(
        "🔊 BGM Volume",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.05,
        help="Adjust background music volume (0.1 = 10%)"
    )
    
    if bgm_file:
        st.sidebar.success(f"✅ BGM uploaded! Volume: {int(bgm_volume * 100)}%")
    else:
        st.sidebar.info("ℹ️ No background music")

    # Main Content Area
    st.markdown("### 📝 Script Generation")
    
    # AI Script Generation Section
    with st.expander("✨ Generate Script with Gemini 2.0 Flash", expanded=True):
        # Script Type Selection
        st.markdown("**📋 Script Type**")
        script_type = st.radio(
            "Choose what to generate:",
            ["sentences", "words"],
            format_func=lambda x: "📝 Sentences (Full phrases)" if x == "sentences" else "🔤 Words (Vocabulary)",
            horizontal=True,
            help="Choose whether to generate full sentences or individual words"
        )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            topic = st.text_input(
                "📚 Topic",
                value="Basic Urdu greetings",
                help="Enter the topic for your video script"
            )
            level = st.selectbox(
                "🎓 Difficulty Level",
                ["beginner", "intermediate", "advanced"],
                index=0,
                help="Choose the learning level"
            )
        
        with col2:
            item_label = "Sentences" if script_type == "sentences" else "Words"
            num_pairs = st.slider(
                f"🔢 Number of {item_label}",
                min_value=1,
                max_value=15,
                value=5,
                help=f"How many {item_label.lower()} to generate"
            )
            st.write("")  # Spacing
            st.write("")  # Spacing
        
        if st.button("🤖 Generate Script with AI", use_container_width=True):
            with st.spinner("🔮 AI is generating your script..."):
                try:
                    pairs = generate_script_with_gemini(
                        topic=topic,
                        level=level,
                        num_pairs=num_pairs,
                        script_type=script_type
                    )
                    st.session_state["script_text"] = json.dumps(pairs, ensure_ascii=False, indent=2)
                    st.success("✅ Script generated successfully!")
                    st.balloons()
                    # Force rerun to update textarea
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    # Script Editor
    st.markdown("---")
    st.markdown("### ✏️ Edit Script")
    
    # Initialize script_text in session state if not present
    if "script_text" not in st.session_state:
        st.session_state["script_text"] = load_example_script()
    
    script_text = st.text_area(
        "JSON Script",
        value=st.session_state["script_text"],
        height=250,
        help="Edit your script in JSON format. Each entry should have 'en' and 'ur' keys."
    )
    
    # Update session state when user edits
    if script_text != st.session_state["script_text"]:
        st.session_state["script_text"] = script_text



    # Video Generation
    st.markdown("---")
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"urdu_video_{timestamp}.mp4"
    output_path = os.path.join(output_dir, output_filename)

    if st.button("🎥 Generate Video", use_container_width=True, type="primary"):
        with st.spinner("🎬 Creating your video... This may take a while."):
            try:
                from app.cleanup import get_temp_script_path, get_temp_image_path, get_temp_audio_path
                
                data = json.loads(script_text)
                
                # Use organized temp directory
                script_path = get_temp_script_path(suffix="_script.json")
                with open(script_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                bg_path = None
                if bg_file is not None:
                    bg_tmp = get_temp_image_path(suffix="_bg.jpg")
                    with open(bg_tmp, "wb") as f:
                        f.write(bg_file.read())
                    bg_path = prepare_background_image(bg_tmp)
                
                # Handle BGM upload
                bgm_path = None
                if bgm_file is not None:
                    bgm_tmp = get_temp_audio_path(suffix="_bgm.mp3")
                    with open(bgm_tmp, "wb") as f:
                        f.write(bgm_file.read())
                    bgm_path = bgm_tmp

                build_video(
                    script_path=script_path,
                    output_path=output_path,
                    background_path=bg_path,
                    bgm_path=bgm_path,
                    bgm_volume=bgm_volume,
                )

                st.success("🎉 Video generated successfully!")
                
                # Display video preview
                st.video(output_path)
                
                # Download button
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Video",
                        data=f,
                        file_name=output_filename,
                        mime="video/mp4",
                        use_container_width=True
                    )

            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format. Please check your script.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
            finally:
                cleanup_temp()
    
    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #a0aec0; font-size: 0.9rem;'>Powered by Gemini 2.0 Flash AI 🚀</p>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
