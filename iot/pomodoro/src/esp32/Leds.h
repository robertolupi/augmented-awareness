//
// Created by Roberto Lupi on 15.02.2025.
//

#ifndef LEDS_H
#define LEDS_H
#include <Pomodoro.h>
#include <FastLED.h>


class Leds : public PomodoroObserver
{
public:
    Leds();
    void notification(::ClockUpdate) override;
    void notification(::IdleToWork) override {}
    void notification(::WorkToBreak) override {}
    void notification(::BreakToIdle) override {}
    void notification(::WorkToIdle) override {}
    void notification(::AdditionalWork) override {}
private:
    constexpr static int kInternalLeds = 10;
    constexpr static int kExternalLeds = 30;

    CRGB internal_leds_[kInternalLeds];
    CRGB external_leds_[kExternalLeds];
};



#endif //LEDS_H
