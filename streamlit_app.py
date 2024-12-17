import streamlit as st
import os
import json
import zipfile
from pathlib import Path
import pandas as pd
import shutil

from powerbi_analyzer import PowerBIAnalyzer

st.title("Power BI Documentation Generator")

st.write("""
Upload a ZIP file containing your PBIP project (the `.SemanticModel` and `.Report` directories, 
along with `.tmdl` and `relationships.tmdl` files).
The app will parse the metadata, generate documentation, and display the relationship diagram.
""")

uploaded_file = st.file_uploader("Upload your PBIP ZIP", type=["zip"])

if uploaded_file is not None:
    # Create a temporary directory to extract files
    temp_dir = Path("temp_extracted")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)  # Safely remove the directory and its contents
    temp_dir.mkdir()

    # Extract the uploaded ZIP
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Specify the base path
    base_path = str(temp_dir)

    # Generate documentation
    analyzer = PowerBIAnalyzer(base_path)
    documentation = analyzer.generate_documentation()

    # Show the relationships diagram if generated
    if os.path.exists("relationships.png"):
        st.image("relationships.png", caption="Table Relationships Diagram")
    else:
        st.write("No diagram found. Check if relationships exist in your model.")

    # Display documentation as structured tables:
    st.write("## Documentation Overview")

    # Tables Summary
    if "tables" in documentation and documentation["tables"]:
        tables_data = [
            {
                "Table Name": t["name"],
                "Columns": len(t["columns"]),
                "Measures": len(t["measures"]),
                "Has PowerQuery": bool(t["powerquery_code"])
            }
            for t in documentation["tables"]
        ]

        st.write("### Tables Summary")
        st.table(pd.DataFrame(tables_data))

        # Columns and measures per table
        for t in documentation["tables"]:
            if t["columns"]:
                st.write(f"#### Columns for {t['name']}")
                st.table(pd.DataFrame(t["columns"]))

            if t["measures"]:
                st.write(f"#### Measures for {t['name']}")
                st.table(pd.DataFrame(t["measures"]))

            if t["powerquery_code"]:
                st.write(f"#### PowerQuery M Code for {t['name']}")
                st.code(t["powerquery_code"], language='m')
    else:
        st.write("No tables found in documentation.")

    # Relationships
    if "relationships" in documentation and documentation["relationships"]:
        st.write("## Relationships")
        st.table(pd.DataFrame(documentation["relationships"]))
    else:
        st.write("No relationships found.")

    # DAX Measures
    if "dax_measures" in documentation and documentation["dax_measures"]:
        st.write("## DAX Measures")
        st.table(pd.DataFrame(documentation["dax_measures"]))

    # Offer downloads for documentation.json and documentation.md
    if os.path.exists("documentation.json"):
        with open("documentation.json", "r", encoding='utf-8') as f:
            doc_json_str = f.read()
        st.download_button(
            label="Download documentation.json",
            data=doc_json_str,
            file_name="documentation.json",
            mime="application/json"
        )

    if os.path.exists("documentation.md"):
        with open("documentation.md", "r", encoding='utf-8') as f:
            doc_md_str = f.read()
        st.download_button(
            label="Download documentation.md",
            data=doc_md_str,
            file_name="documentation.md",
            mime="text/markdown"
        )
