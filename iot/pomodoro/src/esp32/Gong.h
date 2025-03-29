//
// Created by Roberto Lupi on 08.02.2025.
//

#ifndef GONG_H
#define GONG_H

#include <Pomodoro.h>

class Gong final : public PomodoroObserver
{
public:
    Gong()
    = default;

    ~Gong() override
    = default;

    void play();

    void notification(::ClockUpdate) override
    {
    }

    void notification(::IdleToWork) override
    {
        play();
    }

    void notification(WorkToBreak update) override
    {
        play();
    }

    void notification(::BreakToIdle) override
    {
        play();
    }

    void notification(::WorkToIdle) override
    {
    }

    void notification(::AdditionalWork) override
    {
    }
};


#endif //GONG_H
