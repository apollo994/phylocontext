#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from io import StringIO

import pandas as pd
import utils.ncbi_plots as ncbi_plots


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
        command_str = " ".join(datasets_command)
        print(f"\n[ERROR] Command failed: {command_str}", file=sys.stderr)
        print(f"[ERROR] Exit Code: {e.returncode}", file=sys.stderr)
        print(f"[ERROR] stderr:\n{e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    # Load JSON
    datasets_json = {
        str(json.loads(line)["taxonomy"]["tax_id"]): json.loads(line)
        for line in datasets_answer.stdout.strip().splitlines()
    }

    return datasets_json


def get_focus_id_rank(datasets_dict, rank):

    rank_id = datasets_dict["taxonomy"]["classification"][rank]["id"]

    return str(rank_id)


def get_focus_id_level(datasets_dict, level):

    max_level = len(datasets_dict["taxonomy"]["parents"])
    if level > max_level:
        print(
            f"[INFO] max parets level for selected taxid is {max_level}. Defaulting to 3"
        )
        level = 3
    level_id = datasets_dict["taxonomy"]["parents"][-abs(level)]

    return str(level_id)


def get_annotation_count(focus_level, all=False, accept_zero=False):

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
        datasets_command.append("--reference")

    try:
        datasets_answer = subprocess.run(
            datasets_command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    except subprocess.CalledProcessError as e:
        if accept_zero and "no genome data is currently available" in e.stderr:
            return 0
        else:
            print(
                f"[ERROR] Failed to run datasets command:\n{e.stderr}", file=sys.stderr
            )
            sys.exit(1)

    try:
        datasets_json = json.loads(datasets_answer.stdout)
        annotations_count = datasets_json["included_data_files"]["genome_gff"][
            "file_count"
        ]
    except Exception as e:
        print(f"[ERROR] Failed to parse datasets output: {e}", file=sys.stderr)
        sys.exit(1)

    if annotations_count < 1 and not accept_zero:
        print("[ERROR] No annotations found. Try higher level or rank")
        sys.exit(1)

    return annotations_count


def download_annotation(
    focus_level, annotations_dir="annotations_ncbi", zip_name="ncbi_dataset.zip"
):  # follwing formatting rules caused sad face here

    os.makedirs(annotations_dir, exist_ok=True)
    output_path = os.path.join(annotations_dir, zip_name)

    unzipped_path = os.path.splitext(output_path)[0]  # removes ".zip"
    if os.path.exists(unzipped_path):
        print(
            f"[ERROR] Unzipped folder already exists: {unzipped_path}", file=sys.stderr
        )
        sys.exit(1)

    datasets_command = [
        "datasets",
        "download",
        "genome",
        "taxon",
        focus_level,
        "--include",
        "gff3",
        "--reference",
        "--annotated",
        "--filename",
        output_path,
    ]

    try:
        print(f"[INFO] Running command: {subprocess.list2cmdline(datasets_command)}")
        subprocess.run(datasets_command, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to run datasets download: {e}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(output_path):
        print(f"[ERROR] Download failed — {output_path} not found", file=sys.stderr)
        sys.exit(1)

    return output_path


def extract_annotation_zip(zip_path, extract_to=None):

    if extract_to is None:
        extract_to = os.path.splitext(zip_path)[0]

    os.makedirs(extract_to, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"[INFO] Extracted contents to: {extract_to}")

        os.remove(zip_path)
        print(f"[INFO] Removed archive: {zip_path}")

    except zipfile.BadZipFile as e:
        print(f"[ERROR] Invalid ZIP archive: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed during extraction: {e}", file=sys.stderr)
        sys.exit(1)

    return extract_to


def build_assembly_report(base_folder):
    """
    Converts assembly_data_report.jsonl to a pandas DataFrame using `dataformat` CLI.
    """
    data_dir = os.path.join(base_folder, "ncbi_dataset", "data")
    jsonl_path = os.path.join(data_dir, "assembly_data_report.jsonl")

    if not os.path.isfile(jsonl_path):
        print(f"[ERROR] Report file not found: {jsonl_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(jsonl_path, "r") as infile:
            result = subprocess.run(
                ["dataformat", "tsv", "genome"],
                check=True,
                text=True,
                stdin=infile,
                capture_output=True,
            )
        df = pd.read_csv(StringIO(result.stdout), sep="\t")
        print("[INFO] Assembly report parsed into DataFrame")
        return df

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] dataformat command failed: {e}", file=sys.stderr)
        sys.exit(1)


def build_annotation_report(base_folder, input_taxid, focus_taxid):
    """
    Filters the assembly report DataFrame to include only assemblies
    with available annotations, adds relation to input taxons
    and saves the filtered result.
    """
    annotation_dir = os.path.join(base_folder, "annotations_ncbi")
    annotation_report_path = os.path.join(base_folder, "annotations_report.tsv")

    # Get names of annotated assemblies
    assemblies_names = [
        os.path.splitext(name)[0] for name in os.listdir(annotation_dir)
    ]

    # Load full assembly report into a DataFrame
    df = build_assembly_report(base_folder)

    # Filter based on available annotations
    df = df[df["Assembly Accession"].isin(assemblies_names)]
    df = df.drop_duplicates(subset="Assembly Accession", keep="first")  # type: ignore
    df = df.dropna(axis=1, how="all")
    df = df.rename(columns={col: col.replace(" ", "_") for col in df.columns})

    # Add ancestor info
    df_with_distance = add_taxon_distance(df, input_taxid, focus_taxid)

    # Save cleaned report
    df_with_distance.to_csv(annotation_report_path, index=False, sep="\t")
    print(f"[INFO] Annotation report saved to: {annotation_report_path}")

    return df_with_distance


def add_taxon_distance(annotation_report, input_taxid, focus_taxid):
    """
    take an annotation report and enrich each annotation/assemblyit
    with distance from the input_taxid.
    """
    # An alternative implementation could take a input taxiod and
    # a list of taxid, but this would require many ncbi API requests
    # one for each taxon and one for each common ancentor
    # while knowign the focus taxid allows for a single request

    print("[INFO] Collecting last common ancestor (lca) information")
    focus_taxid = str(focus_taxid)

    focus_with_children = get_dataset_json(focus_taxid, children=True)
    annotations_taxid = annotation_report["Organism_Taxonomic_ID"].tolist()
    annotations_taxid = [str(t) for t in annotations_taxid]

    input_taxid_lineage = focus_with_children[input_taxid]["taxonomy"]["parents"]
    input_taxid_lineage.append(input_taxid)
    input_taxid_lineage = [str(t) for t in input_taxid_lineage]

    last_common_ancestor = {k: {} for k in annotations_taxid}

    for ann_taxid in annotations_taxid:
        ann_lineage = focus_with_children[ann_taxid]["taxonomy"]["parents"]
        ann_lineage = [str(t) for t in ann_lineage]

        for lineage in reversed(input_taxid_lineage):
            if lineage in ann_lineage:
                last_common_ancestor[ann_taxid] = {
                    "lca_taxid": lineage,
                    "lca_rank": focus_with_children[lineage]["taxonomy"].get(
                        "rank", ""
                    ),
                    "lca_name": focus_with_children[lineage]["taxonomy"]
                    .get("current_scientific_name", {})
                    .get("name", ""),
                    "lca_starting_from": input_taxid,
                }
                break

    # Create dataframe
    lca_df = pd.DataFrame.from_dict(last_common_ancestor, orient="index")
    lca_df.index.name = "Organism_Taxonomic_ID"
    lca_df.reset_index(inplace=True)

    # Ensure matching types for merge
    annotation_report["Organism_Taxonomic_ID"] = annotation_report[
        "Organism_Taxonomic_ID"
    ].astype(str)
    annotation_report_with_distance = annotation_report.merge(
        lca_df, on="Organism_Taxonomic_ID", how="left"
    )

    return annotation_report_with_distance


def flatten_and_rename_gff(base_folder):
    """
    Reorganizes NCBI dataset folder by moving all genomic.gff files
    into a subfolder called 'annotations', renaming them to their assembly name.
    """
    data_dir = os.path.join(base_folder, "ncbi_dataset", "data")
    annotations_dir = os.path.join(base_folder, "annotations_ncbi")

    if not os.path.isdir(data_dir):
        print(f"[ERROR] Expected data directory not found: {data_dir}")
        return

    os.makedirs(annotations_dir, exist_ok=True)

    for entry in os.listdir(data_dir):
        entry_path = os.path.join(data_dir, entry)

        # Skip non-directories
        if not os.path.isdir(entry_path):
            continue

        gff_path = os.path.join(entry_path, "genomic.gff")
        if os.path.isfile(gff_path):
            new_name = f"{entry}.gff"
            dest_path = os.path.join(annotations_dir, new_name)
            shutil.move(gff_path, dest_path)

            # Remove the now-empty folder
            if not os.listdir(entry_path):
                os.rmdir(entry_path)
        else:
            print(f"[WARNING] No genomic.gff found in {entry}")

    print(f"[INFO] Annotation file(s) moved to: {annotations_dir}")


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
        help="Output folder (default: annotations_ncbi)",
    )

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-l",
        "--level",
        type=int,
        help="Number of taxonomic levels of parents (e.g. 1 means genus)",
    )
    group.add_argument(
        "-r",
        "--rank",
        type=str,
        help="Taxonomic rank to retrieve (e.g. species, genus, family)",
    )

    args = parser.parse_args()

    if args.level is None and args.rank is None:
        args.level = 3  # Default fallback
        print("[INFO] Neither --level nor --rank specified. Defaulting to --level 3")

    ### Main body ##################################################################

    datasets_dict = get_dataset_json(args.taxid)
    input_species_dict = datasets_dict[args.taxid]

    print(f"[INFO] Fetched information for taxon {args.taxid}")

    # Focus id is the taxon id to download annotations
    if args.rank is not None:
        focus_id = str(get_focus_id_rank(input_species_dict, args.rank))
        print(f"[INFO] The requested {args.rank} taxon id is {focus_id}")
    else:
        focus_id = str(get_focus_id_level(input_species_dict, args.level))
        print(f"[INFO] The requested level ({args.level}) taxon id is {focus_id}")

    # Make sure there are at least one annotation available for the focus id
    annotations_count = get_annotation_count(focus_id)
    print(f"[INFO] {annotations_count} annotations found. Downloading them!")

    # Download from NCBI
    zip_path = download_annotation(
        focus_id,
        annotations_dir=args.output,
        zip_name=f"{args.taxid}_to_{focus_id}_ncbi_dataset.zip",
    )

    # extract and reorg
    download_location = extract_annotation_zip(zip_path)
    flatten_and_rename_gff(download_location)

    # build annotation report with lca info
    ann_df = build_annotation_report(download_location, args.taxid, focus_id)

    # make plots
    plots_dir = os.path.join(download_location, "annotations_report_plots")
    os.makedirs(plots_dir)

    ncbi_plots.plot_BUSCO(ann_df, plots_dir)
    ncbi_plots.plot_assembly_stats(ann_df, plots_dir)
    ncbi_plots.plot_gene_stats(ann_df, plots_dir)
    ncbi_plots.plot_assembly_gaps(ann_df, plots_dir)

    print(f"[info] Plots saved at {plots_dir}")

    # clean up
    shutil.rmtree(os.path.join(download_location, "ncbi_dataset"))
    os.remove(os.path.join(download_location, "md5sum.txt"))
    os.remove(os.path.join(download_location, "README.md"))

    print(f"[INFO] Done, results saved in {download_location}")


if __name__ == "__main__":
    main()
