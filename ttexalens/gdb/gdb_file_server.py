# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import io
import os
from ttexalens.context import Context


class GdbFileServer:
    def __init__(self, context: Context):
        self.opened_files: dict[int, io.BufferedIOBase] = dict()
        self._context = context
        self.next_fd = 1

    def __del__(self):
        self.close_all()

    def close_all(self):
        # Close all opened files
        self.opened_files.clear()
        self.next_fd = 0

    def open(self, filename: str, flags: int, mode: int) -> int | str:
        try:
            content = self._context.file_api.get_binary(filename)
            id = self.next_fd

            self.opened_files[id] = content
            self.next_fd += 1
            return id
        except OSError as e:
            return f"-1,{e.errno}"

    def close(self, fd: int) -> bool:
        if fd in self.opened_files.keys():
            del self.opened_files[fd]
            return True
        return False

    def pread(self, fd: int, count: int, offset: int) -> bytes | str:
        if fd in self.opened_files:
            stream = self.opened_files[fd]
            try:
                stream.seek(offset, os.SEEK_SET)
                return stream.read(count)
            except:
                return "-1, Exception while reading."
        else:
            return "-1"

    def pwrite(self, fd: int, offset: int, data: bytes) -> int | bytes | str:
        if fd in self.opened_files:
            stream = self.opened_files[fd]
            try:
                stream.seek(offset, os.SEEK_SET)
                return stream.write(data)
            except:
                return "-2,Error while writing."
        else:
            return "-1"
