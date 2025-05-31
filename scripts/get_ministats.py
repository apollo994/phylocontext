#!/usr/bin/env python3

import argparse
import os
import sys
import pandas as pd
import utils.ministats_utils as ministats_utils


def main():

    parser = argparse.ArgumentParser(
        description="Generate simple statistics from ncbi annotations"
    )

    parser.add_argument(
        "-a",
        "--annotations",
        type=str,
        help="Folder with annotations",
    )

    parser.add_argument(
        "-m",
        "--metadata",
        type=str,
        help="Annotations metadata",
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="Input annotation in gff format",
    )

    parser.add_argument(
        "-is",
        "--input_size",
        type=str,
        help="Input annotation genome size in bp",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=".",
        help="Output folder (default: current dir)",
    )

    args = parser.parse_args()
    
    # check if custom input annotation has genome size
    if args.input:
        if not args.input_size:
            sys.exit("Error: --input_size (-is) must be provided when --input (-i) is specified.")
    

    # Check if output directory exists
    output_dir = os.path.join(args.output, "ministats")
    if os.path.exists(output_dir):
        print(f"[ERROR] Output folder {output_dir} already exists")
        sys.exit(1)
    else:
        os.makedirs(output_dir)

    # Run ministats for ncbi annotations

    print("[INFO] Running ministats on ncbi annotations")
    ncbi_metadata = pd.read_csv(args.metadata, sep="\t")
    annotation_metadata = ncbi_metadata.set_index("Assembly_Accession").to_dict(orient="index")
    annotation_list = [
        a for a in os.listdir(args.annotations) if a.endswith((".gff", "gff3"))
    ]


    for a in annotation_list:
        assembly_name, _ = os.path.splitext(a)
        genome_size = annotation_metadata[assembly_name][
            "Assembly_Stats_Total_Sequence_Length"
        ]
        if genome_size is None:
            print(f"[WARNING] No metadata found for {a}, skipping.")
            continue

        annotation_path = os.path.join(args.annotations, a)
        target = os.path.join(output_dir, f"ministats_{assembly_name}.tsv")
        ministats_utils.run_ministats(annotation_path, genome_size, target)


    # Run ministats for input annotations

    print("[INFO] Running ministats on input annotations")

    input_annotation_name = os.path.basename(args.input).removesuffix(".gff").removesuffix(".gff3")
    target = os.path.join(output_dir, f"ministats_{input_annotation_name}.tsv")
    ministats_utils.run_ministats(args.input, args.input_size, target)

    print(f"[INFO] Ministats saved at {output_dir}")

if __name__ == "__main__":
    main()
