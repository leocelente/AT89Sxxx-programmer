#include <at89s8253.h>
#include <stdint.h>

#define delay() for (uint16_t i = 0; i < 15000; ++i)

int main(void) {
  while (1) {
    P1_0 = 1;
    delay();
    P1_0 = 0;
    delay();
  }
}
