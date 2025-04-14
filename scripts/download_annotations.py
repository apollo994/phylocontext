#!/usr/bin/env python3

import argparse
import subprocess
import json
import sys
import os
import zipfile


def get_dataset_json(tax_id):
    
    datasets_command = ['datasets',
                        'summary',
                        'taxonomy',
                        'taxon',
                        tax_id,
                        '--children',
                        '--as-json-lines'
                        ]
    
    try:
        datasets_answer = subprocess.run(
            datasets_command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to run datasets command: {e}", file=sys.stderr)
        sys.exit(1)

    # Load JSON
    datasets_json = json.loads(datasets_answer.stdout)

    return datasets_json


def get_focus_id_rank(datasets_dict, rank):

    rank_id = datasets_dict['taxonomy']['classification'][rank]['id']
    
    return rank_id

def get_focus_id_level(datasets_dict, level):

    max_level = len(datasets_dict['taxonomy']['parents'])
    if level > max_level:
        print(f"[INFO] max parets level for selected taxid is {max_level}. Defaulting to 3")
        level = 3
    level_id = datasets_dict['taxonomy']['parents'][-abs(level)]

    return level_id

def get_annotation_count(focus_level):

    datasets_command = ['datasets',
                        'download',
                        'genome',
                        'taxon',
                        focus_level,
                        '--include',
                        'gff3',
                        '--reference',
                        '--preview'
                        ]
    
    try:
        datasets_answer = subprocess.run(
            datasets_command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to run datasets command: {e}", file=sys.stderr)
        sys.exit(1)

    datasets_json = json.loads(datasets_answer.stdout)
    annotations_count = datasets_json['included_data_files']['genome_gff']['file_count']
    
    if annotations_count < 1:
        print(f"[ERROR] No annotations found. Try higher level or rank")
        sys.exit(1)
    else:
        return annotations_count

    
def download_annotation(focus_level, annotations_dir='annotations_ncbi', zip_name='ncbi_dataset.zip'):
    
    os.makedirs(annotations_dir, exist_ok=True)
    output_path = os.path.join(annotations_dir, zip_name)

    unzipped_path = os.path.splitext(output_path)[0]  # removes ".zip"
    if os.path.exists(unzipped_path):
        print(f"[ERROR] Unzipped folder already exists: {unzipped_path}", file=sys.stderr)
        sys.exit(1)
    
    datasets_command = ['datasets',
                        'download',
                        'genome',
                        'taxon',
                        focus_level,
                        '--include',
                        'gff3',
                        '--reference',
                        '--filename',
                        output_path
                        ]

    try:
        subprocess.run(
            datasets_command,
            check=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to run datasets download: {e}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(output_path):
        print(f"[ERROR] Download failed — {output_path} not found", file=sys.stderr)
        sys.exit(1)
    
    print (f"[INFO] Command: {subprocess.list2cmdline(datasets_command)}")

    return output_path


def extract_annotation_zip(zip_path, extract_to=None):
    
    if extract_to is None:
        extract_to = os.path.splitext(zip_path)[0]

    os.makedirs(extract_to, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
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




def make_report():
    return 0



def main():

    parser = argparse.ArgumentParser(description='Download annotations of close species to a given taxon')

    parser.add_argument(
        '-t', '--taxid',
        type=str,
        required=True,
        help='NCBI taxonomy identifier (e.g., 9606 for Homo sapiens)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='annotations_ncbi',
        help='Output folder (default: annotations_ncbi)'
    )

    
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '-l', '--level',
        type=int,
        help='Number of taxonomic levels of parents (e.g. 1 means genus)'
    )
    group.add_argument(
        '-r', '--rank',
        type=str,
        help='Taxonomic rank to retrieve (e.g. species, genus, family)'
    )
    
    args = parser.parse_args()

    if args.level is None and args.rank is None:
        args.level = 3  # Default fallback
        print("[INFO] Neither --level nor --rank specified. Defaulting to --level 3")
    
    ### Main body

    datasets_dict = get_dataset_json(args.taxid)
    print(f'[INFO] Fetched information for taxon {args.taxid}')

    if args.rank is not None:
        focus_level = str(get_focus_id_rank(datasets_dict, args.rank))
        print(f'[INFO] The requested {args.rank} taxon id is {focus_level}')

    elif args.level is not None:
        focus_level = str(get_focus_id_level(datasets_dict, args.level))
        print(f'[INFO] The requested level ({args.level}) taxon id is {focus_level}')
    
    annotations_count = get_annotation_count(focus_level)
    print(f'[INFO] {annotations_count} annotations found. Downloading them!')


    zip_path = download_annotation(focus_level, annotations_dir=args.output ,zip_name=f'{focus_level}_ncbi_dataset.zip')
    download_location = extract_annotation_zip(zip_path)
    print(f'[INFO] Annotations downloaded and saved in {download_location}')


if __name__ == "__main__":
    main()
