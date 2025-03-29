//
// Created by Roberto Lupi on 08.02.2025.
//

#include <M5Unified.h>

#include "Gong.h"

extern const unsigned char gong_wav_start[] asm("_binary_gong_wav_start");
extern const unsigned char gong_wav_end[] asm("_binary_gong_wav_end");

void Gong::play() {
    M5.Speaker.playWav(gong_wav_start, gong_wav_end - gong_wav_start);
}