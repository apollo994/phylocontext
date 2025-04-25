# Docker
### Pull the imaage
```
docker pull apollo994/phylocontext:latest
```
### Test the image
```
docker run --rm apollo994/phylocontext:latest get_info --help
```
### Run the scripts
```
# get info
docker run --rm \
    -v $(pwd)/results:/results \
    apollo994/phylocontext \
    get_info -t 6669  -o /results
```

```
# get annotations
docker run --rm \
    -v $(pwd)/results:/results \
    apollo994/phylocontext \
    get_annotations -t 6669 -r genus -o /results
```

# Singularity

### Pull the imaage
```
singularity pull phylocontext.sif docker://apollo994/phylocontext:latest
```
### Test the image
```
singularity run phylocontext.sif get_info --help
```
### Run the scripts
```
# get info
singularity run phylocontext.sif get_info -t 6669 -o results
```

```
# get annotations
singularity run phylocontext.sif get_annotations -t 6669 -r genus -o results
```

