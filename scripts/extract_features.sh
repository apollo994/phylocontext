#!/bin/bash

# Check for input arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <gff_file> <genome_size_in_bp>"
    exit 1
fi

# Input arguments
gff_file="$1"
genome="$2"

# Size is computed removing contig names, counting charachters and subtracting lines (\n)
genome_size_bp=$(awk '{print $2 - $1}' < <(grep -v '^>' $genome | wc -l -c))

# Function to calculate feature stats
calculate_feature_stats() {
    awk -F'\t' '!/^#/ {
        feature_type = $3
        start = $4
        end = $5
        feature_length = end - start + 1

        # Increment the count and total length for this feature type
        count[feature_type]++
        total_length[feature_type] += feature_length
    } END {
       
        # Print the header inside awk
        print "Feature\tFeatures_Count\tTotal_Feature_Length\tAverage_Feature_Length\tGenome_Percentage"
        
        # Print the results for each feature type in a single line, comma-separated
        for (feature in count) {
            avg_length = total_length[feature] / count[feature]
            feature_density_ft = (total_length[feature] / '"$genome_size_bp"') * 100
            
            # Print in CSV format: Feature, Total Features, Average Feature Length, Genome Percentage
            printf "%s\t%d\t%d\t%.2f\t%.2f\n", feature, count[feature], total_length[feature], avg_length, feature_density_ftMb
        }
    }'
}

# Check if the input file is gzipped
if [[ "$gff_file" == *.gz ]]; then
    gunzip -c "$gff_file" | calculate_feature_stats
else
    calculate_feature_stats < "$gff_file"
fi
