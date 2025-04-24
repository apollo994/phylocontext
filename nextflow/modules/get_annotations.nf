process GET_ANNOTATIONS {

    tag "Getting annotation close to ${taxid}"
    publishDir "${params.outdir}", mode: 'copy'

    input:
    val taxid

    output:
    path "results_${taxid}", emit: results

    script:
    """
    mkdir -p results_${taxid}
    get_annotations -t ${taxid} -r genus -o results_${taxid}
    """
}
