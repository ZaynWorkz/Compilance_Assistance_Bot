# app/components/otp_input.py

import streamlit as st

def render_declaration_input():
    """
    Render OTP-style input for declaration number
    Format: XXX-XXXXXXXX-XX
    """
    st.markdown("### Enter Declaration Number")
    
    # Create columns for the three parts
    col1, sep1, col2, sep2, col3 = st.columns([1, 0.2, 3, 0.2, 1])
    
    with col1:
        part1 = st.text_input(
            "First 3 digits",
            key="decl_part1",
            max_chars=3,
            placeholder="101",
            label_visibility="collapsed"
        )
    
    with sep1:
        st.markdown("<h1 style='text-align: center; margin-top: 25px;'>-</h1>", 
                   unsafe_allow_html=True)
    
    with col2:
        part2 = st.text_input(
            "Middle 8 digits",
            key="decl_part2",
            max_chars=8,
            placeholder="25123867",
            label_visibility="collapsed"
        )
    
    with sep2:
        st.markdown("<h1 style='text-align: center; margin-top: 25px;'>-</h1>", 
                   unsafe_allow_html=True)
    
    with col3:
        part3 = st.text_input(
            "Last 2 digits",
            key="decl_part3",
            max_chars=2,
            placeholder="24",
            label_visibility="collapsed"
        )
    
    # Auto-advance logic with JavaScript
    st.markdown("""
    <script>
    // Auto-focus and advance between fields
    const inputs = window.parent.document.querySelectorAll('input[type="text"]');
    for (let i = 0; i < inputs.length - 1; i++) {
        inputs[i].addEventListener('input', function() {
            if (this.value.length === this.maxLength) {
                inputs[i + 1].focus();
            }
        });
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Combine parts
    if part1 and part2 and part3:
        if len(part1) == 3 and len(part2) == 8 and len(part3) == 2:
            full_number = f"{part1}-{part2}-{part3}"
            return full_number
    
    return None