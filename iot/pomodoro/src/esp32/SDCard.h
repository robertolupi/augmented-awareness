//
// Created by Roberto Lupi on 26.02.2025.
//

#ifndef SDCARD_H
#define SDCARD_H

#include <mutex>

/**
 * @brief Class to handle the SD card
 *
 * It privdes access to the SD card using a RAII pattern.
 * If an instance exists, the SD card is mounted, if all instances are destroyed, the SD card is unmounted.
 */
class SDCard {
public:
  SDCard();
  virtual ~SDCard();
  explicit operator bool () const { return mounted; }
private:
  static bool mounted;
  static int instances;
  static std::mutex mutex;
};



#endif //SDCARD_H
