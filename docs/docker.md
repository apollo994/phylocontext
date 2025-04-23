
### Pull the imaage
```
docker pull apollo994/phylocontext:latest
```
### Test the image
```
docker run --rm phylocontext:latest 
```
# Running from outside
### Get info
```
docker run --rm \
    -v $(pwd)/results:/results \
    apollo994/phylocontext \
    get_info.py -t 6669  -o /results
```

### Get annotations
```
docker run --rm \
    -v $(pwd)/results:/results \
    apollo994/phylocontext \
    get_annotations.py -t 6669  -o /results
```
# Running from inside
### Enter the container
```
docker run --rm -it --entrypoint bash apollo994/phylocontext
```
### Run commands
Note `-o results/` fron inside instead of `-o /results` from outside
```
python get_info.py -t 6669  -o results/

#or

python get_annotations.py -t 6669  -o results/
```
