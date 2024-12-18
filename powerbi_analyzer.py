def create_graphviz_relationship_diagram(self, output_file="relationships"):
    """
    Generates a Graphviz relationship diagram with table names as cluster labels
    and column names inside boxes. Adjusts layout to scale proportionally as a square.
    """
    documentation = self.documentation
    dot = Digraph(comment="Table Relationships Diagram", format="png")
    
    # Set graph attributes for proportional layout
    dot.attr(
        rankdir="LR",              # Left-to-right layout (can be "TB" for top-bottom)
        size="10,10",              # Limit graph size to 10x10 inches
        ratio="compress",          # Automatically adjust aspect ratio to make it square
        nodesep="0.75",            # Horizontal spacing between nodes
        ranksep="0.75"             # Vertical spacing between nodes
    )
    dot.attr("graph", fontsize="12", fontname="Arial")
    dot.attr("node", shape="box", fontname="Arial", fontsize="10")

    # Track all involved columns in relationships
    involved_columns = set()
    for rel in documentation["relationships"]:
        involved_columns.add((rel["fromTable"], rel["fromColumn"]))
        involved_columns.add((rel["toTable"], rel["toColumn"]))

    # Create clusters for tables and include only related columns
    for table in documentation["tables"]:
        tname = table["name"]

        # Get related columns for this table
        related_columns = [c["name"] for c in table["columns"] if (tname, c["name"]) in involved_columns]
        fallback_related_cols = [col for (tbl, col) in involved_columns if tbl == tname]

        # Use fallback related columns if explicit matches are not found
        if not related_columns:
            related_columns = fallback_related_cols

        # Deduplicate columns
        related_columns = list(set(related_columns))

        # Create a cluster for the table
        with dot.subgraph(name=f"cluster_{tname}") as c:
            c.attr(
                label=tname,
                labelloc="t",
                fontsize="12",
                fontname="Arial",
                style="filled",
                fillcolor="lightgray",
                color="black"
            )

            # Create nodes for columns
            for col in related_columns:
                c.node(f"{tname}_{col}", label=col, shape="box")

    # Add edges between columns based on relationships
    for rel in documentation["relationships"]:
        from_node = f"{rel['fromTable']}_{rel['fromColumn']}"
        to_node = f"{rel['toTable']}_{rel['toColumn']}"
        dot.edge(from_node, to_node)

    # Render the diagram and save as 'relationships.png'
    output_path = dot.render(output_file, cleanup=True)
    png_path = "relationships.png"
    if os.path.exists(f"{output_file}.png"):
        os.rename(f"{output_file}.png", png_path)
        print(f"Relationship diagram successfully generated and saved as: {png_path}")
    else:
        print("No diagram was generated. Check if relationships exist and try again.")
