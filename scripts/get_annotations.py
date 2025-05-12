#!/usr/bin/env python3

import argparse
import os
import shutil

import utils.ncbi_plots as ncbi_plots
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

    datasets_dict = ncbi_requests.get_dataset_json(args.taxid)
    input_species_dict = datasets_dict[args.taxid]

    print(f"[INFO] Fetched information for taxon {args.taxid}")

    # Focus id is the taxon id to download annotations
    if args.rank is not None:
        focus_id = str(ncbi_requests.get_focus_id_rank(input_species_dict, args.rank))
        print(f"[INFO] The requested {args.rank} taxon id is {focus_id}")
    else:
        focus_id = str(ncbi_requests.get_focus_id_level(input_species_dict, args.level))
        print(f"[INFO] The requested level ({args.level}) taxon id is {focus_id}")

    # Make sure there are at least one annotation available for the focus id
    annotations_count = ncbi_requests.get_annotation_count(focus_id)
    print(f"[INFO] {annotations_count} annotations found. Downloading them!")

    # Download from NCBI
    zip_path = ncbi_requests.download_annotation(
        focus_id,
        annotations_dir=args.output,
        zip_name=f"{args.taxid}_to_{focus_id}_ncbi_dataset.zip",
    )

    # extract and reorg
    download_location = ncbi_requests.extract_annotation_zip(zip_path)
    ncbi_requests.flatten_and_rename_gff(download_location)

    # build annotation report with lca info
    print(download_location)
    ann_df = ncbi_requests.build_annotation_report(download_location, args.taxid, focus_id)

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
