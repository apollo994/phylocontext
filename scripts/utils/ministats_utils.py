#!/usr/bin/env python3
    
import os
import subprocess


def run_ministats(gff_file, genome_size, output_file):

    # get location of the bash script to extract extract_features.sh
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

def get_miniplot(ministats_folder, features = ['gene','mRNA', 'exon', 'CDS']):




    return 0
