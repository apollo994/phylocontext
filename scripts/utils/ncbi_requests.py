#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from io import StringIO

import pandas as pd


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
            command_str = " ".join(datasets_command)
            print(f"\n[ERROR] Command failed: {command_str}", file=sys.stderr)
            print(f"[ERROR] Exit Code: {e.returncode}", file=sys.stderr)
            print(f"[ERROR] stderr:\n{e.stderr.strip()}", file=sys.stderr)
            sys.exit(1)

    try:
        datasets_json = json.loads(datasets_answer.stdout)
        annotations_count = datasets_json["included_data_files"]["genome_gff"][
            "file_count"
        ]
    except Exception as e:
        if accept_zero:
            return 0
        else:
            print(f"[ERROR] Failed to parse datasets output: {e}", file=sys.stderr)
            print(datasets_answer.stdout)
            print("[ERROR] Possibly no annotations were found.")
            print(
                "[ERROR] Run get_info.py and select a rank/level with annotations available "
            )
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

    print(f"[INFO] Looking for JSONL report at: {jsonl_path}")

    if not os.path.isfile(jsonl_path):
        print(f"[ERROR] Report file not found: {jsonl_path}", file=sys.stderr)
        sys.exit(1)

    # The command to be run
    # the assembly_data_report.json contains the "atgcCount" that can not be handled by dataformat
    # adding --force is to overcome this temporarly
    command = ["dataformat", "tsv", "genome", "--force"]

    try:
        print(f"[INFO] Running command: {' '.join(command)} < {jsonl_path}")

        with open(jsonl_path, "r") as infile:
            result = subprocess.run(
                command,
                check=True,
                text=True,
                stdin=infile,
                capture_output=True,
            )
        
        # If we want to see the raw output
        # print("[DEBUG] Raw Output:")
        # print(result.stdout)

        df = pd.read_csv(StringIO(result.stdout), sep="\t")
        print("[INFO] Assembly report parsed into DataFrame")
        return df

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] dataformat command failed with exit code {e.returncode}", file=sys.stderr)
        print(f"[ERROR] Command used: {' '.join(command)}", file=sys.stderr)
        print(f"[ERROR] STDERR output:\n{e.stderr}", file=sys.stderr)
        print(f"[ERROR] STDOUT output:\n{e.stdout}", file=sys.stderr)
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


def get_species_count(children_dataset_dict, parents_id_list):
    """
    Takes a dictionary of taxonomi entries and a list of parents.
    Returns a fictionary with the number of species for each parent.
    """

    species_count_dict = {str(k): 0 for k in parents_id_list}

    for entry in children_dataset_dict:
        rank = children_dataset_dict[entry]["taxonomy"].get("rank", "")

        if rank == "SPECIES":
            species_parents = children_dataset_dict[entry]["taxonomy"]["parents"]
            species_parents = [str(i) for i in species_parents]
            for parent in parents_id_list:
                if parent in species_parents:
                    species_count_dict[parent] += 1
    return species_count_dict


def report_annotation_counts_by_rank(datasets_dict):
    """
    Takes a dataset dictionary of a specic taxon and
    retunr simple statistics
    """
    lineage = datasets_dict["taxonomy"]["classification"]
    parents = datasets_dict["taxonomy"]["parents"]
    report = []
    ranks = ["SPECIES", "GENUS", "FAMILY", "ORDER", "CLASS", "PHYLUM", "KINGDOM"]

    for rank in ranks:
        rank_lower = rank.lower()
        if rank_lower not in lineage:
            print(f"[INFO] {rank} information not found")
            continue
        taxon_info = lineage[rank_lower]
        taxon_id = str(taxon_info["id"])
        taxon_name = taxon_info["name"]
        taxon_level = (
            list(reversed(parents)).index(int(taxon_id)) + 1 if rank != "SPECIES" else 0
        )  # adding one otherise genus would be 0

        count = get_annotation_count(taxon_id, accept_zero=True)
        report.append(
            {
                "rank": rank,
                "level": taxon_level,
                "name": taxon_name,
                "taxon_id": taxon_id,
                "annotation_count": count,
            }
        )

        time.sleep(0.3)  # be nice to NCBI

    return report


def report_annotation_counts_by_parents(datasets_dict, max_parents=6):

    parent_info = []

    input_taxid = datasets_dict["taxonomy"]["tax_id"]

    # Get lineage
    parent_ids = datasets_dict["taxonomy"].get("parents", [])
    parent_ids = [str(i) for i in parent_ids]

    if not parent_ids:
        print("[ERROR] No parent lineage found.")
        sys.exit(1)

    if max_parents > 0:  # Get last N parents (closest first)
        selected_parents = parent_ids[-max_parents:]
        if len(parent_ids) < max_parents:
            print(
                f"[WARNING] Only {len(parent_ids)} parent taxa available (less than {max_parents})"
            )
        # get species count for each parent, use the highest level
        children_dataset_dict = get_dataset_json(selected_parents[0], children=True)
        species_count = get_species_count(children_dataset_dict, selected_parents)
        # Add species taxid as is required for annotaion count
        selected_parents.append(str(input_taxid))
        # Add artificial 1 to species count, this do not accout for subspecies
        species_count[str(input_taxid)] = 1
    else:  # deal with -e 0 when user only wants information about species
        selected_parents = [str(input_taxid)]
        children_dataset_dict = {str(input_taxid): datasets_dict}
        species_count = {str(input_taxid): 1}

    print(f"[INFO] Reporting info for {selected_parents}")
    if len(selected_parents) > 5:
        print("[INFO] High -e values may require long time to compute")

    for pid in reversed(selected_parents):  # Closest parent first
        pid_str = str(pid)
        annotation_count_ref = get_annotation_count(pid_str, accept_zero=True)
        annotation_count_all = get_annotation_count(pid_str, all=True, accept_zero=True)
        pid_dict = children_dataset_dict[pid_str]

        taxonomy = pid_dict.get("taxonomy", {})
        counts = taxonomy.get("counts", [])

        # Get assembly count
        assembly_count = next(
            (c["count"] for c in counts if c["type"] == "COUNT_TYPE_ASSEMBLY"), 0
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
