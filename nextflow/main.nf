nextflow.enable.dsl = 2

include { GET_ANNOTATIONS } from './modules/get_annotations'

// Log pipeline info
log.info """\
         PHYLOCONTEXT PIPELINE
         =====================
         taxids: ${params.taxids}
         outdir: ${params.outdir}
         """
         .stripIndent()

workflow {

    // Create a channel from taxids
    taxon_ids = Channel.of(params.taxids)
    
    // Run annotation process
    GET_ANNOTATIONS(taxon_ids)
}

workflow.onComplete {
    log.info "Pipeline completed at: $workflow.complete"
    log.info "Execution status: ${ workflow.success ? 'OK' : 'failed' }"
}
