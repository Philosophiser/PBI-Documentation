import json
import re
import os
from pathlib import Path
import pandas as pd
from graphviz import Digraph

class PowerBIAnalyzer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        # Find any folder that ends with .SemanticModel and .Report
        self.semantic_model_path = next(self.base_path.glob("*.SemanticModel"), None)
        self.report_path = next(self.base_path.glob("*.Report"), None)
        if not self.semantic_model_path or not self.report_path:
            raise FileNotFoundError("Could not find .SemanticModel or .Report directories in the provided folder.")
        self.documentation = {
            "dax_measures": [],
            "relationships": [],
            "tables": []
        }

        self.column_pattern = re.compile(r'column\s+([^\s{]+)\s*{([^}]+)}', re.MULTILINE | re.DOTALL)
        self.measure_pattern = re.compile(
            r'measure\s+([^\s=]+)\s*=\s*([^\n]+?(?=[\n}]))(?:\s+formatString:\s*([^\n]+))?',
            re.MULTILINE | re.DOTALL
        )
        self.pq_pattern = re.compile(r'source\s*=\s*(.+?)annotation PBI_ResultType = Table', re.DOTALL)
        self.relationship_pattern = None

    def parse_tmdl_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TMDL file {file_path}: {str(e)}")
            return None

    def analyze_tables(self):
        tables_dir = self.semantic_model_path / "definition" / "tables"
        if not tables_dir.exists():
            print(f"Tables directory not found at {tables_dir}")
            return

        for table_file in tables_dir.glob("*.tmdl"):
            content = self.parse_tmdl_file(table_file)
            if not content:
                continue

            table_info = {
                "name": table_file.stem,
                "columns": [],
                "measures": [],
                "powerquery_code": None
            }

            # Extract columns
            for match in self.column_pattern.finditer(content):
                column_name = match.group(1)
                column_props = match.group(2) if match.group(2) else ""
                data_type = re.search(r'dataType:\s*(\w+)', column_props)
                format_string = re.search(r'formatString:\s*([^\n]+)', column_props)
                summarize_by = re.search(r'summarizeBy:\s*(\w+)', column_props)

                column_info = {
                    "name": column_name,
                    "dataType": data_type.group(1) if data_type else None,
                    "formatString": format_string.group(1).strip() if format_string else None,
                    "summarizeBy": summarize_by.group(1) if summarize_by else None
                }
                table_info["columns"].append(column_info)

            # Extract measures
            for match in self.measure_pattern.finditer(content):
                measure_name = match.group(1)
                expression = match.group(2).strip()
                format_string = match.group(3).strip() if match.group(3) else None

                measure_info = {
                    "name": measure_name,
                    "expression": expression,
                    "formatString": format_string
                }
                table_info["measures"].append(measure_info)
                self.documentation["dax_measures"].append({
                    **measure_info,
                    "table": table_file.stem
                })

            # Capture PowerQuery M code
            pq_match = self.pq_pattern.search(content)
            powerquery_code = pq_match.group(1).strip() if pq_match else None
            table_info["powerquery_code"] = powerquery_code

            self.documentation["tables"].append(table_info)

    def analyze_relationships(self):
        rel_file = self.semantic_model_path / "definition" / "relationships.tmdl"
        content = self.parse_tmdl_file(rel_file)
        if not content:
            print("No content found in relationships.tmdl or file not found.")
            return

        print("Raw relationships file content:")
        print(content)

        self.relationship_pattern = re.compile(
            r'relationship\s+(\S+)\s*\n\s*fromColumn:\s*([^.]+)\.([^\s]+)\s*\n\s*toColumn:\s*([^.]+)\.([^\s]+)',
            re.MULTILINE
        )

        found_relationships = False
        for match in self.relationship_pattern.finditer(content):
            rel_info = {
                "name": match.group(1),
                "fromTable": match.group(2),
                "fromColumn": match.group(3),
                "toTable": match.group(4),
                "toColumn": match.group(5)
            }
            self.documentation["relationships"].append(rel_info)
            found_relationships = True

        if not found_relationships:
            print("No relationships found based on the updated regex pattern.")

    def create_graphviz_relationship_diagram(self, output_file="relationships.gv"):
        documentation = self.documentation
        dot = Digraph(comment='Table Relationships Diagram', format='png')
        dot.attr(rankdir='LR', bgcolor="white")
        dot.attr('graph', fontsize="12", fontname="Arial")
        dot.attr('node', shape='box', fontname="Arial", fontsize="10")

        # Extract relationships and columns involved
        involved_columns = set()
        for rel in documentation["relationships"]:
            involved_columns.add((rel["fromTable"], rel["fromColumn"]))
            involved_columns.add((rel["toTable"], rel["toColumn"]))

        # Create a cluster for each table
        for table in documentation["tables"]:
            tname = table["name"]
            related_columns = [c["name"] for c in table["columns"] if (tname, c["name"]) in involved_columns]

            # If no recognized related columns, use fallback from involved_columns
            if not related_columns:
                fallback_related_cols = [col for (tbl, col) in involved_columns if tbl == tname]
                related_columns = fallback_related_cols

            related_columns = list(set(related_columns))  # remove duplicates

            with dot.subgraph(name=f"cluster_{tname}") as c:
                c.attr(
                    label=tname,
                    labelloc='t',
                    fontsize="12",
                    fontname="Arial",
                    fontcolor="black",
                    style="filled",
                    fillcolor="white",
                    color="black",
                    penwidth="1.0"
                )

                # Create one node per column
                if related_columns:
                    for col in related_columns:
                        c.node(f"{tname}_{col}", label=col, shape="box")
                else:
                    # If no columns related, just create an empty node with the table name cluster
                    c.node(f"{tname}_empty", label="", shape="box")

        # Add edges between columns
        for rel in documentation["relationships"]:
            from_node = f"{rel['fromTable']}_{rel['fromColumn']}"
            to_node = f"{rel['toTable']}_{rel['toColumn']}"
            dot.edge(from_node, to_node)

        output_path = dot.render(output_file, cleanup=True)
        png_path = 'relationships.png'
        if os.path.exists(output_file + '.png'):
            os.rename(output_file + '.png', png_path)
            print(f"Relationship diagram successfully generated and saved as: {png_path}")
        else:
            print("No diagram was generated. Check if relationships exist and try again.")

    def generate_documentation(self):
        self.analyze_tables()
        self.analyze_relationships()
        self.create_graphviz_relationship_diagram()  # Generates relationships.png

        # Save to JSON
        with open("documentation.json", "w", encoding='utf-8') as f:
            json.dump(self.documentation, f, indent=4, ensure_ascii=False)

        # Generate Markdown summary
        self.generate_markdown_summary("documentation.md")

        return self.documentation

    def generate_markdown_summary(self, filename="documentation.md"):
        md_lines = []
        md_lines.append(f"# Documentation for {self.project_name}\n")
        md_lines.append("## Tables and Columns\n")
        for table in self.documentation["tables"]:
            md_lines.append(f"### Table: {table['name']}\n")
            md_lines.append("**Columns:**\n")
            for col in table["columns"]:
                md_lines.append(f"- {col['name']} (DataType: {col.get('dataType','Unknown')}, Format: {col.get('formatString','None')})")
            if table["measures"]:
                md_lines.append("\n**Measures:**\n")
                for m in table["measures"]:
                    md_lines.append(f"- {m['name']} = {m['expression']}")
            if table["powerquery_code"]:
                md_lines.append("\n**PowerQuery M Code:**\n")
                md_lines.append("```")
                md_lines.append(table["powerquery_code"])
                md_lines.append("```")

        # Relationships
        if self.documentation["relationships"]:
            md_lines.append("\n## Relationships\n")
            for rel in self.documentation["relationships"]:
                md_lines.append(f"- **{rel['name']}**: {rel['fromTable']}.{rel['fromColumn']} -> {rel['toTable']}.{rel['toColumn']}")
        else:
            md_lines.append("\n## Relationships\nNo relationships found.")

        # Diagram reference
        md_lines.append("\n## Relationship Diagram\n")
        md_lines.append("![Relationships](relationships.png)\n")

        with open(filename, "w", encoding='utf-8') as f:
            f.write("\n".join(md_lines))
