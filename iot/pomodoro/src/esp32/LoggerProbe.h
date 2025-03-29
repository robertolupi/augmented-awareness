//
// Created by Roberto Lupi on 08.02.2025.
//

#ifndef LOGGERPROBE_H
#define LOGGERPROBE_H


#include <M5Unified.h>
#include <esp_log.h>
#include "Pomodoro.h"

class LoggerProbe : public PomodoroObserver {

    const char* TAG = "Pomodoro";

    public:
    LoggerProbe() {
      ESP_LOGI(TAG, "LoggerProbe created");
    }
    ~LoggerProbe() override {
      ESP_LOGI(TAG, "LoggerProbe destroyed");
    }

    void notification(ClockUpdate update) override {
        ESP_LOGI(TAG, "Button pressed: A=%d, B=%d, C=%d EXT=%d PWR=%d", M5.BtnA.wasPressed(), M5.BtnB.wasPressed(), M5.BtnC.wasPressed(), M5.BtnEXT.wasPressed(), M5.BtnPWR.wasPressed());
        ESP_LOGI(TAG, "ClockUpdate: now=%ld, state=%d, remaining_time_in_state=%ld", update.now, update.state, update.remaining_time_in_state);
    }
    void notification(IdleToWork update) override {
        ESP_LOGI(TAG, "IdleToWork: now=%ld", update.now);
    }
    void notification(WorkToBreak update) override {
        ESP_LOGI(TAG, "WorkToBreak: now=%ld, work_duration=%ld", update.now, update.work_duration);
    }
    void notification(BreakToIdle update) override {
        ESP_LOGI(TAG, "BreakToIdle: now=%ld, break_duration=%ld", update.now, update.break_duration);
    }
    void notification(WorkToIdle update) override {
        ESP_LOGI(TAG, "WorkToIdle: now=%ld, cancelled_work_duration=%ld", update.now, update.cancelled_work_duration);
    }
    void notification(AdditionalWork update) override {
        ESP_LOGI(TAG, "AdditionalWork: now=%ld, new_work_duration=%ld", update.now, update.new_work_duration);
    }

};



#endif //LOGGERPROBE_H
