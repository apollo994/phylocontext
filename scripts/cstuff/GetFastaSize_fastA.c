#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#define SZ 1ull << 14

int main() {
  size_t count = 0;
  char s[SZ];
  bool readId = false;
  size_t N;

  while ((N = fread(&s, 1, SZ, stdin)) == SZ) {
    for (size_t i = 0; i < SZ; i++) {
      readId |= (s[i] == '>');
      bool isNewline = (s[i] == '\n');
      count += (!readId && !isNewline);
      readId &= !isNewline;
    }
  }

  for (size_t i = 0; i < N; i++) {
//    printf("%c %u -> %lu\n", s[i], readId, count);
    readId |= (s[i] == '>');
    bool isNewline = (s[i] == '\n');
    count += (!readId && !isNewline);
    readId &= !isNewline;
  }

  printf("%.0lu\n", count);
  return 0;
}
