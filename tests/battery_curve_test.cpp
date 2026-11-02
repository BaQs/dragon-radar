// Battery level from voltage (src/battery_curve.h): ends of the curve, interpolation,
// monotonic, and the USB threshold on the 1.43's VCC reading.
#include "battery_curve.h"

#include <assert.h>

int main() {
    // --- ends of the curve ---
    assert(lipoPercent(4300) == 100);
    assert(lipoPercent(4150) == 100);
    assert(lipoPercent(3300) == 0);
    assert(lipoPercent(3000) == 0);

    // --- exact points and interpolation between them ---
    assert(lipoPercent(3800) == 48);
    assert(lipoPercent(3700) == 15);
    assert(lipoPercent(3975) == 80);                 // halfway between 3950 (77) and 4000 (84)

    // --- never goes up when the voltage goes down ---
    int last = 101;
    for (int mv = 4300; mv >= 3000; mv -= 5) {
        const int p = lipoPercent(mv);
        assert(p >= 0 && p <= 100);
        assert(p <= last);
        last = p;
    }

    // --- USB: the 5 V rail (4.7-5 V on the 1.43), never a charged cell ---
    assert(vccOnUsb(4900));
    assert(vccOnUsb(4600));
    assert(!vccOnUsb(4200));                          // a full cell
    assert(!vccOnUsb(3700));
    return 0;
}
