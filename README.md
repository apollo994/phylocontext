# phylocontext
Provide phylogenetic context to genome annotations

### Obtain annotations frome related species
The goal of this projects is to obtain genome annotations from organisms related to a species of interest. This task is particularly usefull in the context of genome annotation and comparative genomics. This program relies on `datasets` and `dataformat` CLI form [NCBI Datasets](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/) to facilitate the download of the annotations. Species are generally refered as their ncbi taxonomy identifier.

This project is currently under development. 

### Usage

#### Install dependencies
```
git clone https://github.com/apollo994/phylocontext.git
conda env create -f environment.yml
conda activate phylocontext
```

#### Get species information
This step helps in understanding the number of annatation available for the species of interest.
```
python scripts/get_info.py --help
usage: get_info.py [-h] -t TAXID [-o OUTPUT] [-e EXTENDED]

Download NCBI annotations of species related to a given taxon

options:
  -h, --help               show this help message and exit
  -t, --taxid TAXID        NCBI taxonomy identifier (e.g., 9606 for Homo sapiens)
  -o, --output OUTPUT      Output folder (default: annotation_ncbi)
  -e, --extended EXTENDED  Enable extended mode: number of parent levels to include (e.g. 6)
```
##### Example
```
# basic information for taxon 6669
python scripts/get_info.py -t 6669

| rank    | level | name          | taxon_id | annotation_count |
|---------|-------|---------------|----------|------------------|
| SPECIES | 0     | Daphnia pulex | 6669     | 1                |
| GENUS   | 1     | Daphnia       | 6668     | 5                |
| FAMILY  | 2     | Daphniidae    | 77658    | 5                |
| ORDER   | 5     | Diplostraca   | 84337    | 5                |
| CLASS   | 7     | Branchiopoda  | 6658     | 6                |
| PHYLUM  | 11    | Arthropoda    | 6656     | 485              |
| KINGDOM | 17    | Metazoa       | 33208    | 1757             |


# adding -e (extended) and the number of parents level to check returns a more detailed report
python scripts/get_info.py -t 6669 -e 7

| rank       | name          | taxon_id | annotation_count_ref | annotation_count_all | assembly_count | species_count |
|------------|---------------|----------|----------------------|----------------------|----------------|---------------|
| SPECIES    | Daphnia pulex | 6669     | 1                    | 2                    | 7              | 1             |
| GENUS      | Daphnia       | 6668     | 5                    | 9                    | 26             | 251           |
| FAMILY     | Daphniidae    | 77658    | 5                    | 9                    | 28             | 635           |
| INFRAORDER | Anomopoda     | 116561   | 5                    | 9                    | 29             | 1370          |
| SUBORDER   | Cladocera     | 6665     | 5                    | 9                    | 29             | 1594          |
| ORDER      | Diplostraca   | 84337    | 5                    | 9                    | 31             | 1964          |
| SUBCLASS   | Phyllopoda    | 116557   | 5                    | 9                    | 41             | 2214          |
| CLASS      | Branchiopoda  | 6658     | 6                    | 11                   | 51             | 2494          |
```

#### Download annotations
This triggers the download of all the annotations available for organisms close to the species of interest. It aslo generates a report and plots with with informations about the downloaded annotation and relative assemblies. 
```
python scripts/get_annotations.py --help
usage: get_annotations.py [-h] -t TAXID [-o OUTPUT] [-l LEVEL | -r RANK]

Download NCBI annotations of species related to a given taxon

options:
  -h, --help           show this help message and exit
  -t, --taxid TAXID    NCBI taxonomy identifier (e.g., 9606 for Homo sapiens)
  -o, --output OUTPUT  Output folder (default: annotations_ncbi)
  -l, --level LEVEL    Number of taxonomic levels of parents (e.g. 1 means genus)
  -r, --rank RANK      Taxonomic rank to retrieve (e.g. species, genus, family)
```
##### Example
```
# Download all the annotations related to taxon 6669 up to the rank class 
aython scripts/get_annotations.py -t 6669 -l 7
```

