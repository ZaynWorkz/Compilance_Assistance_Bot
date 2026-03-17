# app/components/summary_grid.py

import streamlit as st
import pandas as pd
from datetime import datetime

def render_summary_grid(declaration_number, documents):
    """
    Render grid view summary of all uploaded documents
    """
    
    st.markdown(f"## 📋 Declaration Summary: `{declaration_number}`")
    st.divider()
    
    # Define grid layout
    doc_order = [
        ('declaration', '📄 Declaration'),
        ('invoice', '💰 Invoice'),
        ('packing_list', '📦 Packing List'),
        ('bol_aws', '🚢 BOL/AWS'),
        ('country_of_origin', '🌍 Country of Origin'),
        ('delivery_order', '📋 Delivery Order')
    ]
    
    # Create grid
    for i in range(0, len(doc_order), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(doc_order):
                doc_key, doc_title = doc_order[i + j]
                doc = documents.get(doc_key, {})
                
                with col:
                    with st.container(border=True):
                        st.markdown(f"### {doc_title}")
                        
                        if doc:
                            # File info
                            st.markdown(f"**File:** `{doc.get('filename', 'N/A')}`")
                            
                            # Extracted data based on document type
                            data = doc.get('extracted_data', {})
                            
                            if doc_key == 'declaration':
                                st.markdown(f"📅 Date: {data.get('declaration_date', 'N/A')}")
                                st.markdown(f"🏢 Consignee: {data.get('consignee', 'N/A')[:30]}...")
                                st.markdown(f"⚖️ Weight: {data.get('gross_weight', 'N/A')} kg")
                                
                            elif doc_key == 'invoice':
                                st.markdown(f"🧾 Invoice #: {data.get('invoice_number', 'N/A')}")
                                st.markdown(f"💰 Value: ${data.get('total_value', 'N/A'):,}")
                                st.markdown(f"📦 Items: {len(data.get('items', []))}")
                                
                            elif doc_key == 'packing_list':
                                st.markdown(f"📦 Packages: {data.get('total_packages', 'N/A')}")
                                st.markdown(f"⚖️ Weight: {data.get('gross_weight', 'N/A')} kg")
                                
                            elif doc_key == 'bol_aws':
                                st.markdown(f"✈️ Flight: {data.get('vessel_flight_number', 'N/A')}")
                                st.markdown(f"📍 Port: {data.get('port_of_discharge', 'N/A')}")
                                
                            elif doc_key == 'country_of_origin':
                                st.markdown(f"🌍 Origin: {data.get('origin_country', 'N/A')}")
                                st.markdown(f"📎 Inv Ref: {data.get('referenced_invoice', 'N/A')}")
                                
                            elif doc_key == 'delivery_order':
                                st.markdown(f"📋 DO #: {data.get('delivery_order_number', 'N/A')}")
                            
                            # Status indicator
                            st.markdown("✅ **Verified**")
                            
                        else:
                            st.markdown("⏳ **Pending**")
                            st.markdown("*Not yet uploaded*")
    
    st.divider()
    
    # Submit button
    all_uploaded = all(documents.get(key) for key, _ in doc_order)
    
    if all_uploaded:
        if st.button("✅ SUBMIT FOR APPROVAL", type="primary", use_container_width=True):
            return True
    else:
        st.info("⚠️ Please upload all required documents to submit.")
        st.button("Submit for Approval", disabled=True, use_container_width=True)
    
    return False