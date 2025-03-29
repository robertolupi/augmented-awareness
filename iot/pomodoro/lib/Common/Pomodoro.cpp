//
// Created by Roberto Lupi on 02.02.2025.
//

#include "Pomodoro.h"

bool PomodoroClock::StartWork(const uint8_t flavor, const time_t work_duration, const time_t break_duration, const time_t now)
{
    if (state_ != IDLE)
    {
        return false;
    }
    state_ends_at_ = now + work_duration;
    last_update_at_ = now;
    last_state_change_at_ = now;
    state_ = WORK;
    work_flavor_ = flavor;
    break_duration_ = break_duration;
    const IdleToWork update = {work_flavor_, now};
    notify_observers(update);
    PassageOfTime(now);
    return true;
}

bool PomodoroClock::ExtendWork(const time_t additional_work_duration, const time_t now)
{
    if (state_ != WORK)
    {
        return false;
    }
    state_ends_at_ += additional_work_duration > 0 ? additional_work_duration : break_duration_;
    const AdditionalWork update = {now, work_flavor_, state_ends_at_};
    last_update_at_ = now;
    notify_observers(update);
    PassageOfTime(now);
    return true;
}

bool PomodoroClock::Cancel(const time_t now)
{
    bool result;
    const WorkToIdle work_to_idle = {now, now - last_state_change_at_};
    const BreakToIdle break_to_idle = {now, now - last_state_change_at_};
    switch (state_)
    {
    case WORK:
        state_ = IDLE;
        last_state_change_at_ = now;
        notify_observers(work_to_idle);
        result = true;
        break;
    case BREAK:
        state_ = IDLE;
        last_state_change_at_ = now;
        notify_observers(break_to_idle);
        result = true;
        break;
    case IDLE:
    default:
        result = false;
    }
    PassageOfTime(now);
    return result;
}

void PomodoroClock::PassageOfTime(const time_t now)
{
    bool state_change = (state_ends_at_ != 0) && (now >= state_ends_at_);
    const WorkToBreak work_to_break = {now, state_ends_at_ - last_state_change_at_};
    const BreakToIdle break_to_idle = {now, state_ends_at_ - last_state_change_at_};
    if (state_change)
    {
        switch (state_)
        {
        case WORK:
            state_ = BREAK;
            last_state_change_at_ = now;
            state_ends_at_ = state_ends_at_ + break_duration_;
            work_flavor_ = 0;
            notify_observers(work_to_break);
            break;
        case BREAK:
            state_ = IDLE;
            last_state_change_at_ = state_ends_at_;
            state_ends_at_ = 0;
            work_flavor_ = 0;
            notify_observers(break_to_idle);
            break;
        default:
            break;
        }
    }
    last_update_at_ = now;
    ClockUpdate update = {now, state_, work_flavor_, state_ends_at_ - now};
    notify_observers(update);
}
