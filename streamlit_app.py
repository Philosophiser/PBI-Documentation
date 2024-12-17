import streamlit as st
import os
import json
import zipfile
from pathlib import Path
import pandas as pd
from graphviz import Digraph

# Include the PowerBIAnalyzer class definition and any additional required code here.
# Example:
# from powerbi_analyzer import PowerBIAnalyzer
# For this example, assume you've pasted the class code below or above.

st.title("Power BI Documentation Generator")

st.write("""
Upload a ZIP file containing your PBIP project (`.SemanticModel`, `.Report`, `.tmdl` files).
The app will parse the metadata, generate documentation, and display the relationship diagram.
""")

uploaded_file = st.file_uploader("Upload your PBIP ZIP", type=["zip"])

if uploaded_file is not None:
    # Create a temporary directory to extract files
    temp_dir = Path("temp_extracted")
    if temp_dir.exists():
        # Clear if already exists
        for f in temp_dir.glob("*"):
            if f.is_dir():
                for subf in f.glob("*"):
                    subf.unlink()
                f.rmdir()
            else:
                f.unlink()
        temp_dir.rmdir()
    temp_dir.mkdir()

    # Extract the uploaded ZIP
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Guess or specify the project name
    # If your `.SemanticModel` and `.Report` files are named "PBIP TEST.pbix.SemanticModel" etc., 
    # your project name might be "PBIP TEST.pbix".
    # Adjust this logic as needed to detect the project name automatically.
    project_name = "PBIP TEST.pbix"
    base_path = str(temp_dir)

    # Initialize and run the analyzer
    analyzer = PowerBIAnalyzer(base_path, project_name)
    documentation = analyzer.generate_documentation()

    # Display the relationships diagram
    if os.path.exists("relationships.png"):
        st.image("relationships.png", caption="Table Relationships Diagram")
    else:
        st.write("No diagram found.")

    # Display documentation as structured tables:
    st.write("## Documentation Overview")

    # Tables Summary
    if "tables" in documentation and documentation["tables"]:
        tables_data = []
        for t in documentation["tables"]:
            tables_data.append({
                "Table Name": t["name"],
                "Columns": len(t["columns"]),
                "Measures": len(t["measures"]),
                "Has PowerQuery": bool(t["powerquery_code"])
            })

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
