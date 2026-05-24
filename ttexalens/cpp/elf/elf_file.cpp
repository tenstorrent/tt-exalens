// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "elf_file.hpp"

#include <elfio/elfio.hpp>
#include <ios>
#include <istream>
#include <stdexcept>
#include <streambuf>
#include <utility>

namespace ttexalens::native_elf {

namespace {

// Read-only std::streambuf that views a contiguous span of bytes without
// copying. Used to feed an input span into ELFIO::elfio::load(std::istream&).
// The viewed memory only needs to remain valid for the duration of the load()
// call — ELFIO copies all section data into its own buffers in non-lazy mode.
class SpanStreamBuf : public std::streambuf {
   public:
    explicit SpanStreamBuf(std::span<const std::byte> data) {
        // setg expects char*; we promise the stream is read-only.
        char* begin = const_cast<char*>(reinterpret_cast<const char*>(data.data()));
        setg(begin, begin, begin + data.size());
    }

   protected:
    pos_type seekoff(off_type off, std::ios_base::seekdir dir, std::ios_base::openmode which) override {
        if ((which & std::ios_base::in) == 0) {
            return pos_type(off_type(-1));
        }
        char* base = eback();
        char* target = nullptr;
        switch (dir) {
            case std::ios_base::beg:
                target = base + off;
                break;
            case std::ios_base::cur:
                target = gptr() + off;
                break;
            case std::ios_base::end:
                target = egptr() + off;
                break;
            default:
                return pos_type(off_type(-1));
        }
        if (target < base || target > egptr()) {
            return pos_type(off_type(-1));
        }
        setg(base, target, egptr());
        return pos_type(target - base);
    }

    pos_type seekpos(pos_type pos, std::ios_base::openmode which) override {
        return seekoff(off_type(pos), std::ios_base::beg, which);
    }
};

// Looks up the section by index and throws if out of range — ELFIO's
// Sections::operator[] silently returns nullptr for invalid indices, which
// would make our reference member undefined behaviour.
const ELFIO::section& section_at(const ELFIO::elfio& elf, unsigned int index) {
    ELFIO::section* s = elf.sections[index];
    if (s == nullptr) {
        throw std::out_of_range("ELF section index " + std::to_string(index) + " out of range");
    }
    return *s;
}

}  // namespace

NativeElfSection::NativeElfSection(std::shared_ptr<ELFIO::elfio> elf, unsigned int section_index)
    : elf(std::move(elf)), section(section_at(*this->elf, section_index)) {}

std::string NativeElfSection::name() const { return section.get_name(); }

uint64_t NativeElfSection::address() const { return static_cast<uint64_t>(section.get_address()); }

uint64_t NativeElfSection::size() const { return static_cast<uint64_t>(section.get_size()); }

std::span<const std::byte> NativeElfSection::data() const {
    const char* p = section.get_data();
    size_t sz = static_cast<size_t>(section.get_size());
    if (p == nullptr || sz == 0) {
        return {};
    }
    return {reinterpret_cast<const std::byte*>(p), sz};
}

NativeElfFile::NativeElfFile() : elf(std::make_shared<ELFIO::elfio>()) {}

NativeElfFile::NativeElfFile(const std::string& path) : elf(std::make_shared<ELFIO::elfio>()) {
    if (!elf->load(path, /*is_lazy=*/true)) {
        throw std::runtime_error("Failed to load ELF file: " + path);
    }
    populate_sections();
}

NativeElfFile::NativeElfFile(const std::filesystem::path& path) : NativeElfFile(path.string()) {}

NativeElfFile NativeElfFile::from_bytes(std::span<const std::byte> data) {
    NativeElfFile out;
    SpanStreamBuf buf(data);
    std::istream stream(&buf);

    // load() defaults to is_lazy=false: ELFIO copies every section's bytes
    // into its own per-section buffers during this call, so `data` only needs
    // to stay valid for the duration of the call — no buffer is held after.
    if (!out.elf->load(stream, /*is_lazy=*/false)) {
        throw std::runtime_error("Failed to load ELF from bytes");
    }
    out.populate_sections();
    return out;
}

void NativeElfFile::populate_sections() {
    const unsigned int n = elf->sections.size();
    section_list.reserve(n);
    for (unsigned int i = 0; i < n; ++i) {
        section_list.emplace_back(elf, i);
    }
}

const std::vector<NativeElfSection>& NativeElfFile::sections() const { return section_list; }

std::optional<NativeElfSection> NativeElfFile::get_section_by_name(std::string_view name) const {
    for (const auto& s : section_list) {
        if (s.name() == name) {
            return s;
        }
    }
    return std::nullopt;
}

}  // namespace ttexalens::native_elf
