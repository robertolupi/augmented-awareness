#include <stdexcept>

#include <Arduino.h>
#include <SD.h> // must be included before M5Unified.h
#include <WiFi.h>

#include <M5Unified.h>
#include <esp_log.h>

#include "Configuration.h"
#include "Pomodoro.h"
#include "ClockFace.h"
#include "Splash.h"
#include "Gong.h"
#include "LoggerProbe.h"
#include "Leds.h"

void setup()
{
    M5.begin();
    Serial.begin(115200);
    ESP_LOGI("main", "Pomodoro Timer");

    try
    {
        Splash splash;
        if (!Configuration.load())
            throw std::runtime_error("Failed to load configuration");
        const std::string ssid = Configuration["wifi"]["ssid"];
        if (ssid.empty())
            throw std::runtime_error("WiFi SSID not found");
        const std::string password = Configuration["wifi"]["pass"];
        if (password.empty())
            throw std::runtime_error("WiFi password not found");
        WiFi.begin(ssid.c_str(), password.c_str());
        while (WiFi.status() != WL_CONNECTED)
        {
            delay(500);
        }
        const std::string ntpServer = Configuration["ntp"]["host"];
        if (ntpServer.empty())
            throw std::runtime_error("NTP server not found");
        const std::string timezone = Configuration["ntp"]["tz"];
        configTzTime(timezone.c_str(), ntpServer.c_str());
        // It takes a couple of seconds to have the correct timezone
        delay(2000);
    }
    catch (const std::exception& e)
    {
        M5.Lcd.setTextSize(2);
        M5.Lcd.print(e.what());
        ESP_LOGE("main", "Exception: %s", e.what());
        return;
    }

    PomodoroClock pomodoro;
    // LoggerProbe probe;
    // pomodoro.add_observer(probe);

    ClockFace clock_face;
    Gong gong;
    Leds leds;
    pomodoro.add_observer(clock_face);
    pomodoro.add_observer(gong);
    pomodoro.add_observer(leds);


    while (true)
    {
        bool buttons = M5.BtnA.wasPressed() || M5.BtnB.wasPressed() || M5.BtnC.wasPressed();
        if (!buttons) { pomodoro.PassageOfTime(); }
        else
        {
            switch (pomodoro.State())
            {
            case IDLE:
                if (M5.BtnA.wasPressed())
                {
                    pomodoro.StartWork(0);
                } else if (M5.BtnB.wasPressed())
                {
                    pomodoro.StartWork(1);
                } else if (M5.BtnC.wasPressed())
                {
                    pomodoro.StartWork(2);
                }
                break;
            case WORK:
                if (M5.BtnB.wasPressed())
                {
                    pomodoro.ExtendWork();
                }
                if (M5.BtnC.wasPressed())
                {
                    pomodoro.Cancel();
                }
                break;
            case BREAK:
                if (M5.BtnC.wasPressed())
                {
                    pomodoro.Cancel();
                }
                break;
            }
        }

        // wait for the next second
        const time_t now = time(nullptr);
        do
        {
            M5.update();
            if (M5.BtnA.wasPressed() || M5.BtnB.wasPressed() || M5.BtnC.wasPressed())
            {
                break;
            }
            delay(100);
        }
        while (time(nullptr) <= now);
    }
}

void loop()
{
}
