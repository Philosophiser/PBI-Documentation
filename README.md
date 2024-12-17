# Power BI Documentation Generator with Streamlit

This application allows you to upload a Power BI Project (`.pbip`) folder as a zipped file. It will parse the folder’s `.tmdl` and `relationships.tmdl` files, generate documentation, and display a relationships diagram via a Streamlit web interface.

## Features

- **Upload a `.zip` file** containing your `.SemanticModel` and `.Report` directories along with `.tmdl` and `relationships.tmdl` files.
- **Automatic parsing** of tables, columns, measures, PowerQuery code, and relationships.
- **Visualization** of relationships with a `relationships.png` diagram.
- **Documentation export** as `documentation.json` and `documentation.md`.
- **Interactive tables** displaying extracted metadata in a structured format.

## Requirements

- Python 3.8 or higher (recommended)
- The packages listed in `requirements.txt`:
  - `streamlit`
  - `pandas`
  - `graphviz`
  - `matplotlib` (if still needed)
  
**Note**:  
You must have Graphviz installed on your system for the diagram generation to work correctly. On Debian/Ubuntu:
```bash
sudo apt-get update
sudo apt-get install graphviz
