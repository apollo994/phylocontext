#include <stdio.h>
#include <stdbool.h>

#define SZ (1 << 14)  // 16 KB buffer

int main(void) {
    char s[SZ];
    size_t count = 0;
    bool in_header = false;
    size_t n;

    while ((n = fread(s, 1, SZ, stdin)) > 0) {
        for (size_t i = 0; i < n; ++i) {
            // Switch into header mode
            if (s[i] == '>') {
                in_header = true;
            }
            // End of line resets header mode
            else if (s[i] == '\n') {
                in_header = false;
            }
            // Count only sequence characters
            else if (!in_header) {
                ++count;
            }
        }
    }

    printf("%lu\n", count);
    return 0;
}
