//
// Created by Roberto Lupi on 06.02.2025.
//

#include "ClockFace.h"

inline void ClockFace::notification(ClockUpdate update)
{
  char time_buffer[sizeof("HH:MM:SS")];
  strftime(time_buffer, sizeof(time_buffer), "%H:%M:%S", localtime(&update.now));
  char remaining_time_buffer[sizeof("MM:SS")];
  strftime(remaining_time_buffer, sizeof(remaining_time_buffer), "%M:%S", gmtime(&update.remaining_time_in_state));
  switch(update.state) {
  case IDLE:
    canvas_.fillScreen(BLACK);
    drawTime(time_buffer, WHITE, 0);
    break;
  case WORK:
    canvas_.fillScreen(DARKGREEN);
    drawFlavor(update.work_flavor);
    drawTime(time_buffer, WHITE, 0);
    drawTime(remaining_time_buffer, BLACK, 1);
    break;
  case BREAK:
    canvas_.fillScreen(RED);
    drawTime(time_buffer, WHITE, 0);
    drawTime(remaining_time_buffer, BLACK, 1);
    break;
  }

  canvas_.pushSprite(0, 0);
}

void ClockFace::drawTime(const char* time, int color, int line)
{
  canvas_.setTextColor(color);
  canvas_.setTextSize(1);
  canvas_.setTextFont(7);
  const int padding = canvas_.fontHeight() / 4;
  canvas_.drawCenterString(time, canvas_.width() / 2, canvas_.height() / 2 - (canvas_.fontHeight() + padding) + (canvas_.fontHeight() + padding) * line);
}

void ClockFace::drawFlavor(const uint8_t flavor)
{
  canvas_.setTextColor(DARKGREY);
  canvas_.setTextSize(3);
  canvas_.setTextFont(8);
  canvas_.drawString(String(flavor), 10, 10);
}
