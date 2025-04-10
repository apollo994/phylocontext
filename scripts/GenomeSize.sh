awk '{print $2 - $1}' < <(grep -v '^>' $1 | wc -l -c) 
