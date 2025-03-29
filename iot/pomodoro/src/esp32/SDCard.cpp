//
// Created by Roberto Lupi on 26.02.2025.
//

#include "SDCard.h"
#include <SD.h>
#include <M5Unified.h>

std::mutex SDCard::mutex;
bool SDCard::mounted = false;
int SDCard::instances = 0;

SDCard::SDCard()
{
    std::lock_guard<std::mutex> lock(mutex);
    if (instances == 0)
    {
        if (!SD.begin(M5.getPin(m5::sd_spi_ss)))
        {
            Serial.print("SD Card Mount Failed\n");
        } else {
          mounted = true;
        }
    }
    instances++;
}

SDCard::~SDCard()
{
    std::lock_guard<std::mutex> lock(mutex);
    instances--;
    if (instances == 0)
    {
        SD.end();
        mounted = false;
    }
}