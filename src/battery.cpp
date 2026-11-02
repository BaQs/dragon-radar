// AXP2101 battery readout via XPowersLib. Shares the I2C bus with touch/IMU; only
// read it from the LVGL loop (core 1), not the network task.
#include "battery.h"
#include "config.h"

#include <Arduino.h>

// Boards without an AXP2101 either measure their supply on an ADC pin (the 1.43:
// BOARD_HAS_BAT_ADC, below) or compile to no-ops and report "no battery", which the UI
// already handles.
#if BOARD_HAS_PMIC
#include <Wire.h>
#define XPOWERS_CHIP_AXP2101
#include "XPowersLib.h"

static XPowersPMU PMU;
static bool s_ok = false;

bool battery_begin() {
    s_ok = PMU.begin(Wire, AXP2101_SLAVE_ADDRESS, PIN_I2C_SDA, PIN_I2C_SCL);
    if (s_ok) {
        PMU.enableBattDetection();
        PMU.enableBattVoltageMeasure();
        Serial.println("[batt] AXP2101 ready");
    } else {
        Serial.println("[batt] AXP2101 not found");
    }
    return s_ok;
}

bool battery_present()  { return s_ok && PMU.isBatteryConnect(); }
int  battery_percent()  { return s_ok ? PMU.getBatteryPercent() : -1; }
bool battery_charging() { return s_ok && PMU.isCharging(); }
// USB/DC input present. XPowersLib's isCharging() goes false once the battery is FULL,
// so "present && !charging" reads as discharging on a USB-tethered, full device — which
// needlessly dropped the poll rate to POLL_INTERVAL_BATTERY_MS. isVbusIn() stays true
// while the device is externally powered.
bool battery_vbus_in()  { return s_ok && PMU.isVbusIn(); }

void battery_enable_codec_rail() {
    if (!s_ok) return;
    PMU.setALDO1Voltage(3300);   // ES8311 analog supply (the reference board enables this)
    PMU.enableALDO1();
    Serial.println("[batt] ALDO1 (codec AVDD) enabled @3.3V");
}

void battery_power_off() {
    if (!s_ok) { Serial.println("[batt] power off: no PMIC"); return; }
    Serial.println("[batt] power off");
    Serial.flush();
    PMU.shutdown();
}

#elif BOARD_HAS_BAT_ADC
// The 1.43: VCC through a x3 divider on PIN_BAT_ADC (board header). On battery VCC is the
// cell voltage; with USB in it is the 5 V rail, so the cell can't be read then: the last
// level measured on battery is kept and shown with the charging symbol. There is no
// charger status line to the ESP32, so "charging" means "USB present".
#include "battery_curve.h"

static int      s_mv = -1;          // smoothed VCC (mV)
static int      s_lastPct = -1;     // last level measured on battery
static uint32_t s_lastRead = 0;

static void sample() {
    if (s_lastRead && millis() - s_lastRead < BAT_SAMPLE_MS) return;
    s_lastRead = millis();
    uint32_t sum = 0;
    for (int i = 0; i < 8; ++i) sum += analogReadMilliVolts(PIN_BAT_ADC);
    const int mv = (int)(sum / 8 * BAT_ADC_RATIO);
    // follow a plug/unplug at once, smooth the rest (WiFi bursts make the rail ripple)
    s_mv = (s_mv < 0 || abs(mv - s_mv) > 300) ? mv : (3 * s_mv + mv) / 4;
    if (!vccOnUsb(s_mv)) s_lastPct = lipoPercent(s_mv);
}

bool battery_begin() {
    analogReadResolution(12);
    analogSetPinAttenuation(PIN_BAT_ADC, ADC_11db);
    sample();
    Serial.printf("[batt] VCC %d mV (%s), no PMIC\n", s_mv, vccOnUsb(s_mv) ? "USB" : "battery");
    return false;   // false = no PMIC: no power-off button / endpoint
}
bool battery_present()  { sample(); return vccOnUsb(s_mv) || s_mv > 3000; }
int  battery_percent()  { sample(); return s_lastPct; }
bool battery_charging() { sample(); return vccOnUsb(s_mv); }
bool battery_vbus_in()  { sample(); return vccOnUsb(s_mv); }
void battery_enable_codec_rail() {}
void battery_power_off() {}

#else   // neither a PMIC nor a voltage reading

bool battery_begin()   { Serial.println("[batt] no PMIC on this board"); return false; }
bool battery_present() { return false; }
int  battery_percent() { return -1; }
bool battery_charging(){ return false; }
bool battery_vbus_in() { return false; }
void battery_enable_codec_rail() {}
void battery_power_off() {}

#endif  // BOARD_HAS_PMIC
