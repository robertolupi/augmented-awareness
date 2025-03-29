//
// Created by Roberto Lupi on 06.02.2025.
//

#ifndef CLOCKFACE_H
#define CLOCKFACE_H

#include <M5Unified.h>

#include "Pomodoro.h"

class ClockFace final : public PomodoroObserver
{
public:
    ClockFace() : canvas_(&M5.Lcd)
    {
        canvas_.createSprite(M5.Lcd.width(), M5.Lcd.height());
    }

    ~ClockFace() override
    {
        canvas_.deleteSprite();
    }


    void notification(ClockUpdate update) override;

    void notification(::IdleToWork) override
    {
    }

    void notification(::WorkToBreak) override
    {
    };

    void notification(::BreakToIdle) override
    {
    };

    void notification(::WorkToIdle) override
    {
    };

    void notification(::AdditionalWork) override
    {
    };

private:
    M5Canvas canvas_;

    void drawTime(const char* time, int color, int line);
    void drawFlavor(const uint8_t flavor);
};


#endif //CLOCKFACE_H
