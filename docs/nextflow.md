# Phylocontext Nextflow Module

This Nextflow module wraps the `phylocontext` tool into a reproducible, containerized workflow component. It is designed to be integrated into larger Nextflow pipelines, while also supporting standalone execution for testing and prototyping.

---

## What It Does

Given a NCBI taxon ID, the module:

- Runs `get_annotations` inside a container
- Downloads and processes NCBI genome annotations
- Outputs a structured report (GFFs, plots, TSV summary)

---

## Running a Simple Test

1. **Install Nextflow** (if you haven’t already):

    ```
    curl -s https://get.nextflow.io | bash
    ```

2. **Run the module standalone**:

    ```
    nextflow run main.nf --taxid 9606 --outdir results -profile local
    ```

The `local` profile expects Docker to be installed and running.  
If Docker is not available, you can instead run this workflow by activating the `phylocontext` Conda environment manually and ensuring that the `get_annotations` command is available in your `PATH`.
