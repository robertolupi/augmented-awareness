//
// Created by Roberto Lupi on 08.02.2025.
//

#include "Splash.h"

#include <M5Unified.h>

extern const unsigned char pomodoro_red_splash_jpeg_start[] asm("_binary_pomodoro_red_splash_jpeg_start");
extern const unsigned char pomodoro_red_splash_jpeg_end[] asm("_binary_pomodoro_red_splash_jpeg_end");


Splash::Splash() {
  M5.Lcd.drawJpg(pomodoro_red_splash_jpeg_start, pomodoro_red_splash_jpeg_end - pomodoro_red_splash_jpeg_start, 0, 0);
}

Splash::~Splash() {
  M5.Lcd.fillScreen(BLACK);
}