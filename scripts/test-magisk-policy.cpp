// SPDX-License-Identifier: GPL-3.0-or-later
#include "rmx2121_magisk.h"
#include <cassert>
#include <fstream>
#include <functional>
#include <iostream>
#include <iterator>
#include <vector>

struct PackageFixture {
    std::vector<uint8_t> bytes;
    bool fail_read = false;
    uint64_t GetPackageSize() const { return bytes.size(); }
    bool UpdateHashAtOffset(const std::vector<std::function<void(const uint8_t*, uint64_t)>>& callbacks,
                            uint64_t offset, uint64_t length) {
        if (fail_read || offset + length > bytes.size()) return false;
        for (const auto& callback : callbacks) callback(bytes.data() + offset, length);
        return true;
    }
};

int main(int argc, char** argv) {
    assert(argc == 2);
    std::ifstream input(argv[1], std::ios::binary);
    assert(input.good());
    PackageFixture package{{std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()}};
    assert(Rmx2121VerifyPinnedMagisk(&package));
    assert(Rmx2121PinnedMagiskPath("/FFiles/OF_Magisk/Magisk.zip", true));
    assert(Rmx2121PinnedMagiskPath("/FFiles/OF_Magisk/uninstall.zip", true));
    assert(!Rmx2121PinnedMagiskPath("/FFiles/OF_Magisk/Magisk.zip", false));
    assert(!Rmx2121PinnedMagiskPath("/sdcard/Fox/FoxFiles/Magisk.zip", true));
    assert(!Rmx2121PinnedMagiskPath("/FFiles/OF_Magisk/Other.zip", true));
    package.bytes[1024] ^= 1; // Same length, CRC/signature-independent corruption.
    assert(!Rmx2121VerifyPinnedMagisk(&package));
    package.bytes[1024] ^= 1;
    package.fail_read = true;
    assert(!Rmx2121VerifyPinnedMagisk(&package));
    package.fail_read = false;
    package.bytes.pop_back();
    assert(!Rmx2121VerifyPinnedMagisk(&package));
    assert(!Rmx2121VerifyPinnedMagisk<PackageFixture>(nullptr));
    std::cout << "Official addon accepted; modified/truncated/unreadable data and untrusted paths rejected\n";
}
