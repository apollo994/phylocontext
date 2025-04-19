#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
import pandas as pd
import tabulate


def get_dataset_json(tax_id, children=False):
    """
    By default the dictionary contains one key which is tax_id.
    When children is true, it returns a dictionary of as many keys
    of children available for taxid.
    """

    datasets_command = [
        "datasets",
        "summary",
        "taxonomy",
        "taxon",
        str(tax_id),
        "--as-json-lines",
    ]

    if children:
        datasets_command.append("--children")

    try:
        datasets_answer = subprocess.run(
            datasets_command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to run datasets command: {e}", file=sys.stderr)
        sys.exit(1)

    # Load JSON
    datasets_json = {
        str(json.loads(line)["taxonomy"]["tax_id"]): json.loads(line)
        for line in datasets_answer.stdout.strip().splitlines()
    }

    return datasets_json


def get_annotation_count(focus_level, all=False):

    datasets_command = [
        "datasets",
        "download",
        "genome",
        "taxon",
        focus_level,
        "--include",
        "gff3",
        "--preview",
        "--annotated",
    ]

    if not all:
        datasets_command.append('--reference')
        
    try:
        datasets_answer = subprocess.run(
            datasets_command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to run datasets command: {e}", file=sys.stderr)
        sys.exit(1)

    datasets_json = json.loads(datasets_answer.stdout)
    annotations_count = datasets_json["included_data_files"]["genome_gff"]["file_count"]

    if annotations_count < 1:
        print("[ERROR] No annotations found. Try higher level or rank")
        sys.exit(1)
    else:
        return annotations_count


def get_species_count(children_dataset_dict, parents_id_list):
    """
    Takes a dictionary of taxonomi entries and a list of parents.
    Returns a fictionary with the number of species for each parent.
    """

    species_count_dict = {str(k): 0 for k in parents_id_list}

    for entry in children_dataset_dict:
        rank = children_dataset_dict[entry]["taxonomy"].get("rank", '')

        if rank == "SPECIES":
            species_parents = children_dataset_dict[entry]["taxonomy"]["parents"]
            species_parents = [str(i) for i in species_parents]
            for parent in parents_id_list:
                if parent in species_parents:
                    species_count_dict[parent] += 1
    return species_count_dict


def report_annotation_counts_by_rank(datasets_dict):

    lineage = datasets_dict["taxonomy"]["classification"]

    report = []
    ranks = ["SPECIES", "GENUS", "FAMILY"]
    # ranks = ['SPECIES', 'GENUS', 'FAMILY', 'ORDER', 'CLASS', 'PHYLUM', 'KINGDOM']

    for rank in ranks:
        rank_lower = rank.lower()
        if rank_lower not in lineage:
            print(f"[INFO] {rank} information not found")
            continue
        taxon_info = lineage[rank_lower]
        taxon_id = str(taxon_info["id"])
        taxon_name = taxon_info["name"]

        try:
            count = get_annotation_count(taxon_id)
        except SystemExit:
            count = "NA"

        report.append(
            {
                "rank": rank,
                "name": taxon_name,
                "taxon_id": taxon_id,
                "annotation_count": count,
            }
        )

        time.sleep(0.3)  # be nice to NCBI

    return report


def report_annotation_counts_by_parents(datasets_dict, max_parents=6):

    parent_info = []

    # Get lineage
    parent_ids = datasets_dict["taxonomy"].get("parents", [])
    parent_ids = [str(i) for i in parent_ids]

    if not parent_ids:
        print("[ERROR] No parent lineage found.")
        sys.exit(1)

    # Get last N parents (closest first)
    selected_parents = parent_ids[-max_parents:]
    if len(parent_ids) < max_parents:
        print(
            f"[WARNING] Only {len(parent_ids)} parent taxa available (less than {max_parents})"
        )

    # get species count for each parent, use the highest level
    children_dataset_dict = get_dataset_json(selected_parents[0], children=True)
    species_count = get_species_count(children_dataset_dict, selected_parents)

    for pid in reversed(selected_parents):  # Closest parent first
        pid_str = str(pid)

        annotation_count_ref = get_annotation_count(pid_str)
        annotation_count_all = get_annotation_count(pid_str, all=True)
        pid_dict = children_dataset_dict[pid_str]

        taxonomy = pid_dict.get("taxonomy", {})
        counts = taxonomy.get("counts", [])

        # Get assembly count
        assembly_count = next(
            (c["count"] for c in counts if c["type"] == "COUNT_TYPE_ASSEMBLY"), "NA"
        )
        rank = taxonomy.get("rank", "").upper()
        name = taxonomy.get("current_scientific_name", {}).get("name", "")

        parent_info.append(
            {
                "rank": rank,
                "name": name,
                "taxon_id": pid_str,
                "annotation_count_ref": annotation_count_ref,
                "annotation_count_all": annotation_count_all,
                "assembly_count": assembly_count,
                "species_count": species_count[pid_str],
            }
        )

        time.sleep(0.3)

    return parent_info


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
        default="annotation_ncbi",
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
    datasets_dict = get_dataset_json(args.taxid)
    input_species_dict = datasets_dict[args.taxid]

    if args.extended is not None:
        report = report_annotation_counts_by_parents(input_species_dict, args.extended)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{args.taxid}_infoEXT_{timestamp}.tsv"
        output_path = os.path.join(args.output, output_filename)
    else:
        report = report_annotation_counts_by_rank(input_species_dict)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{args.taxid}_info_{timestamp}.tsv"
        output_path = os.path.join(args.output, output_filename)

    print()
    print(tabulate.tabulate(report, headers="keys"))
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
