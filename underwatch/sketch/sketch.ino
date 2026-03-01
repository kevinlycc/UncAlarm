#include <Arduino_LED_Matrix.h>

uint8_t warning[104] = {
    0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,0,1,1,0,0,1,1,1,1,1,0,0,
    0,0,1,1,0,0,1,1,1,1,1,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,0,1,1,0,0,1,1,1,1,1,0,0,
    0,0,1,1,0,0,1,1,1,1,1,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0
};

Arduino_LED_Matrix matrix;

void setup() {
    matrix.begin();
    matrix.setGrayscaleBits(1);
    matrix.draw(warning);
}

void loop() {
    matrix.setGrayscaleBits(0);
    delay(2000);
    matrix.setGrayscaleBits(1);
    matrix.draw(warning);
    delay(2000);
}