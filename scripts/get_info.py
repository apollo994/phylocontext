#!/usr/bin/env python3

import argparse
import os
import sys
from datetime import datetime

import pandas as pd
import tabulate
import utils.ncbi_requests as ncbi_requests

def main():

    parser = argparse.ArgumentParser(
        description="Download NCBI annotations of species related to a given taxon"
    )

    parser.add_argument(
        "-t",
        "--taxid",
        type=str,
        required=True,
        help="NCBI taxonomy identifier (e.g., 9606 for Homo sapiens)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="annotations_ncbi",
        help="Output folder (default: annotation_ncbi)",
    )

    parser.add_argument(
        "-e",
        "--extended",
        type=int,
        default=None,
        help="Enable extended mode: number of parent levels to include (e.g. 6)",
    )

    args = parser.parse_args()

    ### main body

    # Ensure output directory exists
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    else:
        print(f"[INFO] Output directory exists: {args.output}")

    # Get input taxon dictionary
    datasets_dict = ncbi_requests.get_dataset_json(args.taxid)
    input_species_dict = datasets_dict[args.taxid]

    if args.extended is not None:
        report = ncbi_requests.report_annotation_counts_by_parents(input_species_dict, args.extended)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{args.taxid}_infoEXT{args.extended}_{timestamp}.tsv"
        output_path = os.path.join(args.output, output_filename)
    else:
        report = ncbi_requests.report_annotation_counts_by_rank(input_species_dict)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{args.taxid}_info_{timestamp}.tsv"
        output_path = os.path.join(args.output, output_filename)

    print()
    print(tabulate.tabulate(report, headers="keys"))
    print("(Subspecies are ignored in species count)")
    print()

    # Check if that exact file exists
    if os.path.exists(output_path):
        print(f"[ERROR] Output file already exists: {output_path}")
        sys.exit(1)

    # Save DataFrame
    df = pd.DataFrame(report)
    df.to_csv(output_path, sep="\t", index=False)
    print(f"[INFO] Saved annotation report to: {output_path}")


if __name__ == "__main__":
    main()
