#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import pandas as pd


def get_assembly_metadata(metadata):

    df = pd.read_csv(metadata, sep="\t")
    assembly_dict = df.set_index("Assembly Accession").to_dict(orient="index")

    return assembly_dict


def run_ministats(gff_file, genome_size, output_file):

    # get location of the bash script to extract extract_features.sh
    # assumes is in the same as this script
    script_path = os.path.join(os.path.dirname(__file__), "extract_features.sh")
    command = ["bash", str(script_path), str(gff_file), str(genome_size)]

    try:
        with open(output_file, "w") as out_f:
            subprocess.run(
                command, stdout=out_f, stderr=subprocess.PIPE, text=True, check=True
            )

        print(f"[INFO] Processing {gff_file}")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error processing {gff_file}")
        print(e.stderr)

    except Exception as e:
        print(f"[ERROR] Unexpected error processing {gff_file}: {e}")

    return 0


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
        "-o",
        "--output",
        type=str,
        default=".",
        help="Output folder (default: current dir)",
    )

    args = parser.parse_args()

    # add check to make sure all annotation have metadata

    annotation_metadata = get_assembly_metadata(args.metadata)
    annotation_list = [
        a for a in os.listdir(args.annotations) if a.endswith((".gff", "gff3"))
    ]

    # Check if output directory exists
    output_dir = os.path.join(args.output, "ministats")
    if os.path.exists(output_dir):
        print("[ERROR] Output folder already exists")
        sys.exit(1)
    else:
        os.makedirs(output_dir)

    # Run ministats for each annotation
    for a in annotation_list:
        assembly_name, _ = os.path.splitext(a)
        genome_size = annotation_metadata[assembly_name][
            "Assembly Stats Total Sequence Length"
        ]
        if genome_size is None:
            print(f"[WARNING] No metadata found for {a}, skipping.")
            continue

        annotation_path = os.path.join(args.annotations, a)
        target = os.path.join(output_dir, f"ministats_{assembly_name}.tsv")
        run_ministats(annotation_path, genome_size, target)

    print(f"[INFO] Ministats saved at {output_dir}")


if __name__ == "__main__":
    main()
