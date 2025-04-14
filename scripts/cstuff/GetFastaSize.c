#include <stdio.h>

int main() {

  unsigned long count;
  char current;

  count = 0;

  while ((current = getchar()) != EOF) {

    if (current == '>') {
      while ((current = getchar()) != '\n')
        ;
    }

    if (current != '\n')
      ++count;
  }
  printf("%.0lu\n", count);
  return 0;
}
