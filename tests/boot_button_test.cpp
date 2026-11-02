// BOOT button (src/boot_button.h): short press, long press, contact bounce, and the hold that
// woke the radar from deep sleep. One update() is one loop pass, every TICK ms here.
#include "boot_button.h"

#include <assert.h>
#include <stdint.h>
#include <vector>

static const uint32_t TICK = 5;

struct Run {
    BootButton b;
    uint32_t now = 1000;
    std::vector<BootButton::Event> events;
    explicit Run(bool armed = true) : b(armed) {}
    // Hold the pin at `pressed` for ms, recording every event.
    void level(bool pressed, uint32_t ms) {
        for (uint32_t t = 0; t < ms; t += TICK) {
            now += TICK;
            const BootButton::Event e = b.update(pressed, now);
            if (e != BootButton::NONE) events.push_back(e);
        }
    }
    int count(BootButton::Event e) const {
        int n = 0;
        for (BootButton::Event x : events) n += (x == e);
        return n;
    }
};

int main() {
    // --- short press: PRESS when it goes down, SHORT_PRESS when it comes up, nothing else ---
    {
        Run r;
        r.level(false, 200);
        r.level(true, 300);
        assert(r.count(BootButton::PRESS) == 1);
        assert(r.count(BootButton::SHORT_PRESS) == 0);
        r.level(false, 200);
        assert(r.count(BootButton::SHORT_PRESS) == 1);
        assert(r.count(BootButton::LONG_PRESS) == 0);
        assert(r.events.size() == 2);
    }

    // --- contact bounce shorter than the debounce is ignored ---
    {
        Run r;
        r.level(false, 200);
        for (int i = 0; i < 5; ++i) { r.level(true, 10); r.level(false, 10); }
        r.level(false, 200);
        assert(r.events.empty());
    }

    // --- a bouncy press still counts once ---
    {
        Run r;
        r.level(false, 200);
        r.level(true, 10); r.level(false, 10); r.level(true, 10); r.level(false, 5);
        r.level(true, 400);
        r.level(false, 10); r.level(true, 5);
        r.level(false, 200);
        assert(r.count(BootButton::PRESS) == 1);
        assert(r.count(BootButton::SHORT_PRESS) == 1);
    }

    // --- long press: fires once, while still held, and is not also a short press ---
    {
        Run r;
        r.level(false, 200);
        r.level(true, BOOT_BTN_LONG_MS - 100);
        assert(r.count(BootButton::LONG_PRESS) == 0);
        const float p = r.b.holdProgress(r.now);
        assert(p > 0.9f && p < 1.0f);
        r.level(true, 200);
        assert(r.count(BootButton::LONG_PRESS) == 1);
        assert(r.b.holdProgress(r.now) == 0.0f);     // the ring empties once it has fired
        r.level(true, 3000);                          // keep holding: still only one
        assert(r.count(BootButton::LONG_PRESS) == 1);
        r.level(false, 200);
        assert(r.count(BootButton::SHORT_PRESS) == 0);
        assert(!r.b.down());
    }

    // --- woken from deep sleep by a hold: that hold is ignored, even past the long press ---
    {
        Run r(false);
        r.level(true, BOOT_BTN_LONG_MS + 1500);
        assert(r.events.empty());
        assert(r.b.holdProgress(r.now) == 0.0f);
        r.level(false, 200);
        assert(r.events.empty());                     // letting go of it is not a short press
        r.level(true, 300);                           // the next press works normally
        r.level(false, 200);
        assert(r.count(BootButton::PRESS) == 1);
        assert(r.count(BootButton::SHORT_PRESS) == 1);
    }

    // --- built unarmed, but the button was already up: arms by itself ---
    {
        Run r(false);
        r.level(false, 100);
        r.level(true, BOOT_BTN_LONG_MS + 50);
        assert(r.count(BootButton::LONG_PRESS) == 1);
    }

    // --- millis() wrap-around during a hold ---
    {
        Run r;
        r.now = 0xFFFFFFFFu - 1000;
        r.level(false, 200);
        r.level(true, BOOT_BTN_LONG_MS + 100);
        assert(r.count(BootButton::LONG_PRESS) == 1);
    }

    return 0;
}
