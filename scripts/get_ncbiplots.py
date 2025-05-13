#!/usr/bin/env python3

import argparse
import os
import sys
import pandas as pd
import utils.ncbi_plots as ncbi_plots

def main():

    parser = argparse.ArgumentParser(
        description="Stand alone script to plot summary metrics from ncbi annotation_report.tsv"
    )

    parser.add_argument(
        "-r",
        "--report",
        type=str,
        help="annotation_report.tsv",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=".",
        help="Output folder (default: current dir)",
    )

    args = parser.parse_args()

    # Check if output directory exists
    if not args.report:
        print ("[ERROR] Please specify a annotation_report.tsv")
        sys.exit(0)

    output_dir = os.path.join(args.output, "annotation_report_plots")
    if os.path.exists(output_dir):
        print("[ERROR] Output folder already exists")
        sys.exit(1)
    else:
        os.makedirs(output_dir)

    df = pd.read_csv(args.report, sep="\t")
    df = df.rename(columns={col: col.replace(" ", "_") for col in df.columns})

    ncbi_plots.plot_BUSCO(df, output_dir)
    ncbi_plots.plot_annotations_info(df, output_dir)
    ncbi_plots.plot_assembly_stats(df, output_dir)
    ncbi_plots.plot_gene_stats(df, output_dir)
    ncbi_plots.plot_assembly_gaps(df, output_dir)

    print(f"[info] Plots saved at {output_dir}")

if __name__ == "__main__":
    main()
