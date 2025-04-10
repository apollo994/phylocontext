#include <stdio.h>

#define IN 1
#define OUT 0

int main(){
    
    unsigned long  count;
    int current, head;
    
    count = 0;

    while ((current = getchar()) != EOF){
        
        if (current == '>')
            head = IN;
        else if (head == IN && current != '\n')
            ;
        else if (head == IN && current == '\n')
            head = OUT;
        else if (head == OUT && current != '\n')
            ++count;
        else if (head == OUT && current == '\n')
            ;
    }
    
    printf("%.0lu\n", count);
    return 0; 
}
