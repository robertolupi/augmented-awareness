//
// Created by Roberto Lupi on 01.02.2025.
//

#ifndef CONFIGURATION_H
#define CONFIGURATION_H

#include <string>
#include <unordered_map>

class ConfigurationClass
{
public:
    bool load();

    typedef std::unordered_map<std::string, std::string> Section;

    Section& operator[](const std::string& section)
    {
        return sections[section];
    }

    const Section& operator[](const std::string& section) const
    {
        return sections.at(section);
    }

private:
    std::unordered_map<std::string, Section> sections;
};

extern ConfigurationClass Configuration;


#endif //CONFIGURATION_H
