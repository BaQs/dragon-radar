#pragma once
// Battery level from a voltage, for boards that only measure it (no PMIC fuel gauge), like
// the 1.43. Pure logic, so tests/battery_curve_test.cpp checks it on the host.
//
// The 1.43 measures its VCC rail, not the cell itself: on battery VCC is the cell voltage
// (behind the power-path MOSFET), with USB plugged in it is the 5 V rail. Above
// BAT_USB_MV the reading cannot be a LiPo, so it means "on USB".
#include <stdint.h>
#include "config.h"

// Single LiPo cell under the radar's load (WiFi + panel, a few hundred mA): the voltage
// sags a little below the resting curve, so the points sit about 50 mV lower than a
// datasheet's open-circuit table. Linear between points.
static const int16_t LIPO_CURVE[][2] = {   // { mV, % }
    {4150, 100}, {4100, 95}, {4050, 90}, {4000, 84}, {3950, 77}, {3900, 70}, {3860, 62},
    {3830, 55},  {3800, 48}, {3780, 41}, {3760, 34}, {3740, 27}, {3720, 21}, {3700, 15},
    {3680, 10},  {3640, 6},  {3580, 3},  {3450, 1},  {3300, 0},
};

inline int lipoPercent(int mv) {
    const int n = (int)(sizeof(LIPO_CURVE) / sizeof(LIPO_CURVE[0]));
    if (mv >= LIPO_CURVE[0][0]) return 100;
    if (mv <= LIPO_CURVE[n - 1][0]) return 0;
    for (int i = 1; i < n; ++i) {
        const int v1 = LIPO_CURVE[i][0];
        if (mv >= v1) {
            const int v0 = LIPO_CURVE[i - 1][0], p0 = LIPO_CURVE[i - 1][1], p1 = LIPO_CURVE[i][1];
            return p1 + (p0 - p1) * (mv - v1) / (v0 - v1);
        }
    }
    return 0;
}

// VCC above what a LiPo can give: the board runs on USB.
inline bool vccOnUsb(int mv) { return mv > BAT_USB_MV; }
