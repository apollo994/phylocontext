#include <fcntl.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "Usage: %s <fasta_file>\n", argv[0]);
    return 1;
  }

  int fd = open(argv[1], O_RDONLY);
  if (fd == -1) {
    perror("open");
    return 1;
  }

  struct stat st;
  if (fstat(fd, &st) == -1) {
    perror("fstat");
    close(fd);
    return 1;
  }

  size_t size = st.st_size;
  char *data = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
  close(fd);
  if (data == MAP_FAILED) {
    perror("mmap");
    return 1;
  }

  size_t count = 0;
  bool in_header = false;

  for (size_t i = 0; i < size; ++i) {
    char c = data[i];
    if (c == '>') {
      in_header = true;
    } else if (c == '\n') {
      in_header = false;
    } else if (!in_header) {
      ++count;
    }
  }

  munmap(data, size);
  printf("%lu\n", count);
  return 0;
}
