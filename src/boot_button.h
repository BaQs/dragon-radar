#pragma once
// BOOT button (PIN_BOOT_BUTTON, GPIO0): press / short press / long press from raw pin
// readings. On a radar case the button sits behind the crown, so it is the one physical
// control: a short press steps the zoom, a long press puts the radar to sleep (main.cpp).
// Pure logic, so tests/boot_button_test.cpp drives it on the host; main.cpp's loop feeds it
// the pin level on every pass.
//
// The hold that woke the radar from deep sleep is still down when the loop starts. Built
// with armed = false, the button ignores that press (no PRESS, no LONG_PRESS, no
// SHORT_PRESS) until it has been seen released once, so switching the radar on does not
// switch it straight off again two seconds later.
#include <stdint.h>
#include "config.h"

class BootButton {
public:
    enum Event : uint8_t {
        NONE,
        PRESS,          // went down (after the debounce)
        SHORT_PRESS,    // let go before BOOT_BTN_LONG_MS
        LONG_PRESS,     // held BOOT_BTN_LONG_MS: reported once, while still held
    };

    explicit BootButton(bool armed = true) : _armed(armed) {}

    // One reading: pressed = pin low. At most one event per call.
    Event update(bool pressed, uint32_t nowMs) {
        if (pressed != _raw) { _raw = pressed; _rawSince = nowMs; }
        const bool settled = nowMs - _rawSince >= BOOT_BTN_DEBOUNCE_MS;

        if (settled && _raw != _down) {             // a debounced change
            _down = _raw;
            if (_down) {
                _downSince = _rawSince;              // the hold counts from the first edge
                _fired = false;
                return _armed ? PRESS : NONE;
            }
            const bool counted = _armed && !_fired;  // not the wake-up hold, not after a long press
            _armed = true;
            return counted ? SHORT_PRESS : NONE;
        }
        if (settled && !_down) _armed = true;       // seen released: arm (start-up with no hold)
        if (_down && _armed && !_fired && nowMs - _downSince >= BOOT_BTN_LONG_MS) {
            _fired = true;
            return LONG_PRESS;
        }
        return NONE;
    }

    // How far the current hold has got towards LONG_PRESS: 0..1, and 0 when the button is
    // up, ignored (wake-up hold) or the long press has already fired.
    float holdProgress(uint32_t nowMs) const {
        if (!_down || !_armed || _fired) return 0.0f;
        const uint32_t held = nowMs - _downSince;
        return held >= BOOT_BTN_LONG_MS ? 1.0f : (float)held / (float)BOOT_BTN_LONG_MS;
    }

    bool down() const { return _down; }

private:
    bool     _armed;
    bool     _raw = false;      // last reading
    bool     _down = false;     // debounced state
    bool     _fired = false;    // LONG_PRESS reported for the current hold
    uint32_t _rawSince = 0;     // when the reading last changed
    uint32_t _downSince = 0;    // start of the current hold
};
