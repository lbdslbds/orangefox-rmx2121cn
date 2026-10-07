// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
#include <cstring>
#include <openssl/sha.h>

inline bool Rmx2121PinnedMagiskPath(const char* path, bool built_in) {
    return built_in &&
        (std::strcmp(path, "/FFiles/OF_Magisk/Magisk.zip") == 0 ||
         std::strcmp(path, "/FFiles/OF_Magisk/uninstall.zip") == 0);
}

template <typename PackageType>
bool Rmx2121VerifyPinnedMagisk(PackageType* package) {
    // Unmodified official v30.7 asset, SHA256 e0d32d21...ae9ebd5.
    if (!package || package->GetPackageSize() != 11613864) return false;
    static const uint8_t expected[SHA256_DIGEST_LENGTH] = {
        0xe0,0xd3,0x2d,0x21,0x23,0x53,0x28,0x60,0xf9,0x71,0x23,0xd9,0x27,0xb1,0xbb,0x86,
        0xc4,0xe0,0x8e,0x6f,0xd8,0xa4,0x8b,0xfc,0x6b,0x5b,0xee,0x0a,0xfa,0xe9,0xeb,0xd5
    };
    SHA256_CTX ctx;
    if (SHA256_Init(&ctx) != 1) return false;
    bool updated = true;
    if (!package->UpdateHashAtOffset({[&](const uint8_t* data, uint64_t size) {
        if (SHA256_Update(&ctx, data, size) != 1) updated = false;
    }}, 0, package->GetPackageSize()) || !updated) return false;
    uint8_t digest[SHA256_DIGEST_LENGTH];
    return SHA256_Final(digest, &ctx) == 1 &&
           std::memcmp(digest, expected, sizeof(expected)) == 0;
}
