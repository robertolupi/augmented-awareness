//
// Created by Roberto Lupi on 02.02.2025.
//

#include <ctime>

#ifndef POMODORO_H
#define POMODORO_H

#include <etl/observer.h>

enum PomodoroState
{
    // States (also used for passage of time updates)
    IDLE = 1,
    WORK = 2,
    BREAK = 4,
};

struct ClockUpdate
{
    time_t now;
    PomodoroState state;
    uint8_t work_flavor;
    time_t remaining_time_in_state;
};

struct IdleToWork
{
    uint8_t work_flavor;
    time_t now;
};

struct WorkToBreak
{
    time_t now;
    time_t work_duration;
};

struct BreakToIdle
{
    time_t now;
    time_t break_duration;
};

struct WorkToIdle
{
    time_t now;
    time_t cancelled_work_duration;
};

struct AdditionalWork
{
    time_t now;
    uint8_t work_flavor;
    time_t new_work_duration;
};

typedef etl::observer<ClockUpdate, IdleToWork, WorkToBreak, BreakToIdle, WorkToIdle, AdditionalWork> PomodoroObserver;

constexpr int MAX_POMODORO_OBSERVERS = 5;
constexpr time_t WORK_DEFAULT_DURATION_SECONDS = 25 * 60;
constexpr time_t BREAK_DEFAULT_DURATION_SECONDS = 5 * 60;

class PomodoroClock : public etl::observable<PomodoroObserver, MAX_POMODORO_OBSERVERS>
{
public:
    explicit PomodoroClock() : last_update_at_(0), last_state_change_at_(0), state_ends_at_(0), state_(IDLE)
    {
    }

    bool StartWork(uint8_t flavor, time_t work_duration = WORK_DEFAULT_DURATION_SECONDS, time_t break_duration = BREAK_DEFAULT_DURATION_SECONDS, time_t now = time(nullptr));
    bool ExtendWork(time_t additional_work_duration = 0, time_t now = time(nullptr));
    bool Cancel(time_t now = time(nullptr));
    void PassageOfTime(time_t now = time(nullptr));

    inline PomodoroState State() const
    {
        return state_;
    }

private:
    time_t last_update_at_;
    time_t last_state_change_at_;
    time_t state_ends_at_;
    uint8_t work_flavor_;
    PomodoroState state_;
    time_t break_duration_;
};

#endif //POMODORO_H
