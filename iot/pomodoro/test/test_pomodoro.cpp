#include <unity.h>
#include "Pomodoro.h"

class TestObserver : public PomodoroObserver {
public:
    void reset() {
        clock_updates = 0;
        idle_to_work = 0;
        work_to_break = 0;
        break_to_idle = 0;
        work_to_idle = 0;
        additional_work = 0;
        last_state = IDLE;
        last_remaining_time = 0;
        last_work_flavor = 0;
    }

    void notification(ClockUpdate update) override {
        clock_updates++;
        last_state = update.state;
        last_remaining_time = update.remaining_time_in_state;
        last_work_flavor = update.work_flavor;
    }

    void notification(IdleToWork update) override {
        idle_to_work++;
        last_work_flavor = update.work_flavor;
    }

    void notification(WorkToBreak update) override {
        work_to_break++;
        last_work_duration = update.work_duration;
    }

    void notification(BreakToIdle update) override {
        break_to_idle++;
        last_break_duration = update.break_duration;
    }

    void notification(WorkToIdle update) override {
        work_to_idle++;
        last_cancelled_duration = update.cancelled_work_duration;
    }

    void notification(AdditionalWork update) override {
        additional_work++;
        last_new_work_duration = update.new_work_duration;
        last_work_flavor = update.work_flavor;
    }

    int clock_updates = 0;
    int idle_to_work = 0;
    int work_to_break = 0;
    int break_to_idle = 0;
    int work_to_idle = 0;
    int additional_work = 0;
    PomodoroState last_state = IDLE;
    time_t last_remaining_time = 0;
    uint8_t last_work_flavor = 0;
    time_t last_work_duration = 0;
    time_t last_break_duration = 0;
    time_t last_cancelled_duration = 0;
    time_t last_new_work_duration = 0;
};

TestObserver observer;
PomodoroClock pomodoro;

void setUp(void) {
    observer.reset();
    pomodoro = PomodoroClock();
    pomodoro.add_observer(observer);
}

void test_initial_state(void) {
    TEST_ASSERT_EQUAL(IDLE, pomodoro.State());
}

void test_start_work(void) {
    time_t now = 1000;
    bool result = pomodoro.StartWork(1, 1500, 300, now);
    
    TEST_ASSERT_TRUE(result);
    TEST_ASSERT_EQUAL(WORK, pomodoro.State());
    TEST_ASSERT_EQUAL(1, observer.idle_to_work);
    TEST_ASSERT_EQUAL(1, observer.last_work_flavor);
    TEST_ASSERT_EQUAL(1500, observer.last_remaining_time);
}

void test_start_work_when_not_idle(void) {
    pomodoro.StartWork(1, 1500, 300, 1000);
    bool result = pomodoro.StartWork(2, 1500, 300, 1100);
    
    TEST_ASSERT_FALSE(result);
    TEST_ASSERT_EQUAL(1, observer.idle_to_work);
}

void test_extend_work(void) {
    time_t now = 1000;
    pomodoro.StartWork(1, 1500, 300, now);
    bool result = pomodoro.ExtendWork(600, now + 500);
    
    TEST_ASSERT_TRUE(result);
    TEST_ASSERT_EQUAL(1, observer.additional_work);
    TEST_ASSERT_EQUAL(1600, observer.last_remaining_time);
}

void test_extend_work_when_not_working(void) {
    bool result = pomodoro.ExtendWork(600, 1000);
    
    TEST_ASSERT_FALSE(result);
    TEST_ASSERT_EQUAL(0, observer.additional_work);
}

void test_cancel_work(void) {
    time_t now = 1000;
    pomodoro.StartWork(1, 1500, 300, now);
    bool result = pomodoro.Cancel(now + 500);
    
    TEST_ASSERT_TRUE(result);
    TEST_ASSERT_EQUAL(IDLE, pomodoro.State());
    TEST_ASSERT_EQUAL(1, observer.work_to_idle);
    TEST_ASSERT_EQUAL(500, observer.last_cancelled_duration);
}

void test_cancel_break(void) {
    time_t now = 1000;
    pomodoro.StartWork(1, 1500, 300, now);
    pomodoro.PassageOfTime(now + 1500); // Trigger work to break transition
    bool result = pomodoro.Cancel(now + 1600);
    
    TEST_ASSERT_TRUE(result);
    TEST_ASSERT_EQUAL(IDLE, pomodoro.State());
    TEST_ASSERT_EQUAL(1, observer.break_to_idle);
    TEST_ASSERT_EQUAL(100, observer.last_break_duration);
}

void test_work_to_break_transition(void) {
    time_t now = 1000;
    pomodoro.StartWork(1, 1500, 300, now);
    pomodoro.PassageOfTime(now + 1500);
    
    TEST_ASSERT_EQUAL(BREAK, pomodoro.State());
    TEST_ASSERT_EQUAL(1, observer.work_to_break);
    TEST_ASSERT_EQUAL(1500, observer.last_work_duration);
    TEST_ASSERT_EQUAL(300, observer.last_remaining_time);
}

void test_break_to_idle_transition(void) {
    time_t now = 1000;
    pomodoro.StartWork(1, 1500, 300, now);
    pomodoro.PassageOfTime(now + 1500); // Work to break
    pomodoro.PassageOfTime(now + 1800); // Break to idle
    
    TEST_ASSERT_EQUAL(IDLE, pomodoro.State());
    TEST_ASSERT_EQUAL(1, observer.break_to_idle);
    TEST_ASSERT_EQUAL(300, observer.last_break_duration);
}

int main(int argc, char **argv) {
    UNITY_BEGIN();
    RUN_TEST(test_initial_state);
    RUN_TEST(test_start_work);
    RUN_TEST(test_start_work_when_not_idle);
    RUN_TEST(test_extend_work);
    RUN_TEST(test_extend_work_when_not_working);
    RUN_TEST(test_cancel_work);
    RUN_TEST(test_cancel_break);
    RUN_TEST(test_work_to_break_transition);
    RUN_TEST(test_break_to_idle_transition);
    return UNITY_END();
}