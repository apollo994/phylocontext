#!/usr/bin/env python3

import argparse
import subprocess
import json
import sys


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


def get_id_classification(datasets_dict, tax_id):
    
    for c in datasets_dict['taxonomy']['classification'].keys():
        print (tax_id)
        print ( datasets_dict['taxonomy']['classification'][c])

        if datasets_dict['taxonomy']['classification'][c]['id'] == int(tax_id):

            return datasets_dict['classification'][c][id] 


def get_annotation_count():
    return 0

def download_annotaion():
    return 0

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

    parser.add_argument(
        '-l', '--level',
        type=int,
        default=3,
        help='Taxonomic level to retrieve (default: 3, i.e., Species, Genus, Family)'
    )


    args = parser.parse_args()

    datasets_dict = get_dataset_json(args.taxid)
    
    higher_id = datasets_dict['taxonomy']['parents'][-abs(args.level)]
    higher_id_info = get_id_classification(datasets_dict, higher_id)
    print (higher_id_info) 




if __name__ == "__main__":
    main()
