//
// Created by Roberto Lupi on 01.02.2025.
//

#include <fstream>

#include "Configuration.h"
#include "SDCard.h"

ConfigurationClass Configuration;

bool ConfigurationClass::load()
{
    SDCard with_sd_card;
    if (!with_sd_card)
    {
        return false;
    }

    std::ifstream file("/sd/config.ini");
    if (!file.is_open())
    {
        return false;
    }

    std::string line;
    std::string section;
    while (std::getline(file, line))
    {
        line.erase(line.find_last_not_of(" \n\r\t") + 1);
        if (line.empty())
        {
            continue;
        }
        if (line[0] == '[' && line[line.size() - 1] == ']')
        {
            section = line.substr(1, line.size() - 2);
            continue;
        }
        const auto pos = line.find('=');
        if (pos == std::string::npos)
        {
            continue;
        }
        std::string key = line.substr(0, pos);
        std::string value = line.substr(pos + 1);
        sections[section][key] = value;
    }
    return true;
}
