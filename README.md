# phylocontext
Provide phylogenetic context to genome annotations

### What about annotations in close species?
The goal of this projects is to obtain genome annotations from organisms related to a species of interest. This task is particularly usefull in the context of genome annotation and comparative genomics. This program relies on `datasets` and `dataformat` CLI form [NCBI Datasets](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/) to facilitate the download of the annotations. Specie are generally refered as their ncbi taxonomy identifier.

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

# adding -e (extended) and the number of parents level to check returns a more detailed report
python scripts/get_info.py -t 6669 -e 7

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

