//
// Created by Roberto Lupi on 15.02.2025.
//

#include <M5Unified.h>

#include "Leds.h"

Leds::Leds()
{
    FastLED.addLeds<WS2812, 15, GRB>(internal_leds_, 10);
    FastLED.addLeds<SK6812, 26, GRB>(external_leds_, 30);
    FastLED.setBrightness(200);
    FastLED.clear();
}

void Leds::notification(ClockUpdate update)
{
    RGBColor color;
    switch (update.state)
    {
    case IDLE:
        color = RGBColor(0, 0, 0);
        break;
    case WORK:
        color = RGBColor(0, 255, 0);
        break;
    case BREAK:
        color = RGBColor(255, 0, 0);
        break;
    }
    for (int i = 0; i < kInternalLeds; i++)
    {
        internal_leds_[i] = CRGB(color.r, color.g, color.b);
    }
    for (int i = 0; i < kExternalLeds; i++)
    {
        external_leds_[i] = CRGB(color.r, color.g, color.b);
    }
    FastLED.show();
}
