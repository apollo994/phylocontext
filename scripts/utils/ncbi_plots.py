#!/usr/bin/env python3

from datetime import datetime

import seaborn as sns
from matplotlib import pyplot as plt


def build_filename(target, title):

    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    filename = f"{target}/{timestamp}_{title}.png"

    return filename


def plot_BUSCO(df, target):

    species_col = "Organism_Name"
    cols = [
        "Annotation_BUSCO_Single_Copy",
        "Annotation_BUSCO_Duplicated",
        "Annotation_BUSCO_Fragmented",
        "Annotation_BUSCO_Missing",
        "Annotation_BUSCO_Complete",
        "Annotation_BUSCO_Total_Count",
        "lca_rank",
    ]

    starting_taxon = str(df["lca_starting_from"].unique()[0])

    # Prepare the data: include all species, fill NaNs with 0
    plot_df = df[[species_col] + cols].copy()
    plot_df[cols] = plot_df[cols].fillna(0)
    plot_df["Organism_label"] = plot_df["Organism_Name"] + "\n" + plot_df["lca_rank"]

    # Rename columns for plotting
    plot_df = plot_df.rename(
        columns={
            "Annotation_BUSCO_Single_Copy": "Single-Copy (S)",
            "Annotation_BUSCO_Duplicated": "Duplicated (D)",
            "Annotation_BUSCO_Fragmented": "Fragmented (F)",
            "Annotation_BUSCO_Missing": "Missing (M)",
            "Annotation_BUSCO_Complete": "Complete (C)",
            "Annotation_BUSCO_Total_Count": "Total (n)",
        }
    )

    # Plotting categories
    plot_order = ["Single-Copy (S)", "Duplicated (D)", "Fragmented (F)", "Missing (M)"]

    # Set colors
    colors = {
        "Single-Copy (S)": "#00BFFF",
        "Duplicated (D)": "#1E90FF",
        "Fragmented (F)": "yellow",
        "Missing (M)": "red",
    }

    # Plot
    plt.figure()
    fig, ax = plt.subplots(figsize=(14, len(plot_df) * 0.6))

    bottom = [0] * len(plot_df)
    for col in plot_order:
        ax.barh(
            plot_df["Organism_label"],
            plot_df[col],
            left=bottom,
            label=col,
            color=colors[col],
        )
        # update bottom
        bottom = [a + b for a, b in zip(bottom, plot_df[col])]

    # Add summary labels at the start of the bar
    for i, row in plot_df.iterrows():

        total = int(row["Total (n)"])
        label = (
            f"C:{int(round(row['Complete (C)']*total))} "
            f"[S:{int(round(row['Single-Copy (S)']*total))}, D:{int(round(row['Duplicated (D)']*total))}], "
            f"F:{int(round(row['Fragmented (F)']*total))}, M:{int(round(row['Missing (M)']*total))}, "
            f"n:{total}"
        )
        ax.text(
            x=0.01,  # small offset to right of the y-axis
            y=i,
            s=label,
            va="center",
            ha="left",
            fontsize=7,
            color="black" if total > 0 else "gray",
            fontfamily="monospace",
        )

    # Final formatting
    ax.set_xlabel("BUSCOs fraction")
    ax.set_title(f"BUSCO Assessment Results (species close to: {starting_taxon})")
    ax.invert_yaxis()
    ax.set_xlim(0, 1.01)
    ax.legend(title="Category", bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.tight_layout()

    # Saving
    fig.savefig(build_filename(target, "BUSCO"), dpi=300, bbox_inches="tight")
    plt.close()

    return 0


def plot_annotations_info(df, target):
    """
    NOT IN USE AS IT'S HARD TO PREDICT TABLE SHAPE
    """
    table_df = df[
        [
            "Organism_Name",
            "Organism_Taxonomic_ID",
            "Annotation_Method",
            "Annotation_Provider",
            "Annotation_Release_Date",
            "lca_rank",
        ]
    ].copy()
    table_df.reset_index(drop=True, inplace=True)

    # Create the figure — height scales with number of rows
    plt.figure()
    fig, ax = plt.subplots(
        figsize=(18, len(table_df) * 0.5)
    )  # Adjust width/height as needed

    ax.axis("off")  # Hide plot axes

    # Create table
    table = plt.table(
        cellText=table_df.values,
        colLabels=table_df.columns,
        loc="center",
        cellLoc="left",
    )

    # Formatting for readability
    table.auto_set_font_size(False)
    table.set_fontsize(16)
    table.scale(1.2, 1.5)  # Adjust scaling to help with long text

    plt.tight_layout()

    # Saving
    fig.savefig(build_filename(target, "summary_table"), dpi=300, bbox_inches="tight")
    plt.close()

    return 0


def plot_assembly_stats(df, target):

    variables = [
        "Assembly_Stats_Total_Sequence_Length",
        "Assembly_Stats_GC_Percent",
        "Assembly_Stats_Total_Number_of_Chromosomes",
        "Assembly_Stats_Number_of_Contigs",
        "Assembly_Stats_Contig_L50",
        "Assembly_Stats_Contig_N50",
        "Assembly_Stats_Number_of_Scaffolds",
        "Assembly_Stats_Scaffold_L50",
        "Assembly_Stats_Scaffold_N50",
    ]

    # Reshape to long format for seaborn
    plot_df = df[["Organism_Name", "lca_rank"] + variables].copy()
    plot_df = plot_df.melt(
        id_vars=["Organism_Name", "lca_rank"],
        value_vars=variables,
        var_name="Metric",
        value_name="Value",
    )
    plot_df["Metric"] = plot_df["Metric"].str.replace("Assembly_Stats_", "")
    plot_df["Organism_label"] = plot_df["Organism_Name"] + "\n" + plot_df["lca_rank"]

    # Create FacetGrid using catplot
    plt.figure()
    g = sns.catplot(
        data=plot_df,
        kind="bar",
        x="Value",
        y="Organism_Name",
        hue="lca_rank",
        col="Metric",
        col_wrap=3,
        height=4,
        aspect=1.5,
        sharey=True,
        sharex=False,
    )

    # Improve formatting
    g.set_titles("{col_name}", size = 18)
    g.set_axis_labels("Value", "")
    g.set(xscale="linear")
    for ax in g.axes.flatten():
        ax.grid(True, axis="x", linestyle="--", alpha=0.3)
        ax.tick_params(axis="y", labelsize=16)

    # Legend
    g._legend.set_title("LCA Rank")
    g._legend.set_loc("upper right")
    g._legend.set_frame_on(True)

    fig = g.figure
    fig.suptitle("Assembly Overview", fontsize=16, y=1.01)
    plt.tight_layout()

    # Saving
    g.savefig(build_filename(target, "assembly_stats"), dpi=300, bbox_inches="tight")
    plt.close()

    return 0


def plot_gene_stats(df, target):

    count_vars = [
        "Annotation_Count_Gene_Non-coding",
        "Annotation_Count_Gene_Protein-coding",
        "Annotation_Count_Gene_Pseudogene",
        "Annotation_Count_Gene_Total",
    ]

    # Prepare data and melt into long format
    plot_df = df[["Organism_Name", "lca_rank"] + count_vars].copy()
    plot_df = plot_df.melt(
        id_vars=["Organism_Name", "lca_rank"],
        value_vars=count_vars,
        var_name="Metric",
        value_name="Value",
    )

    # Clean up 'Metric' labels
    plot_df["Metric"] = plot_df["Metric"].str.replace(
        "Annotation_Count_Gene_", "", regex=False
    )

    # Create the multi-panel plot
    plt.figure()
    g = sns.catplot(
        data=plot_df,
        kind="bar",
        x="Value",
        y="Organism_Name",
        hue="lca_rank",
        col="Metric",
        col_wrap=2,
        sharey=True,
        height=4,
        aspect=1.5,
    )

    # Final touches
    g.set_titles("{col_name}", size = 18)
    g.set_axis_labels("Gene count", "")
    for ax in g.axes.flatten():
        ax.grid(True, axis="x", linestyle="--", alpha=0.3)
        ax.tick_params(axis="y", labelsize=16)

    g._legend.set_title("LCA Rank")
    g._legend.set_loc("upper right")
    g._legend.set_frame_on(True)

    fig = g.figure
    fig.suptitle("Gene Count Overview", fontsize=16, y=1.01)

    plt.tight_layout()

    # Saving
    g.savefig(build_filename(target, "gene_stats"), dpi=300, bbox_inches="tight")
    plt.close()
    return 0


def plot_assembly_gaps(df, target):
    

    x_var = 'Assembly_Stats_Total_Sequence_Length'
    y_var = 'Assembly_Stats_Total_Ungapped_Length'

    fig, ax = plt.subplots(figsize=(8, 6))

    # Create scatterplot
    sns.scatterplot(
        data=df,
        x=x_var,
        y=y_var,
        hue='Organism_Name',
        style='lca_rank',
        s=60,
        ax=ax
    )

    # Clean axis labels
    ax.set_xlabel(x_var.replace('Assembly_Stats_', '').replace('_', ' '))
    ax.set_ylabel(y_var.replace('Assembly_Stats_', '').replace('_', ' '))

    # Set log scale
    ax.set_xscale('log')
    ax.set_yscale('log')

    # Diagonal x=y reference line
    shortest = df[y_var].min()
    longest = df[x_var].max()
    ax.plot(
        [shortest, longest],
        [shortest, longest],
        ls='--',
        linewidth=1,
        c='black',
        alpha=0.5
    )

    # Annotate gap
    for _, row in df.iterrows():
        x = row[x_var]
        y = row[y_var]
        gap = int(x) - int(y)

        # Use offset to avoid overlap, safe for log scale
        ax.annotate(
            f"[gaps = {gap}]",
            xy=(x, y),
            xytext=(5, 0),
            textcoords='offset points',
            fontsize=7,
        )


    ax.legend(loc='best')
    ax.set_title("Gaps and Sequence Length", fontsize=14)
    plt.tight_layout()

    # Saving
    plt.savefig(build_filename(target, "assembly_gaps"), dpi=150, bbox_inches="tight")
    plt.close()

    return 0
