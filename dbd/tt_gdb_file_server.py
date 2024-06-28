# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import io
import os

class GdbFileServer:
    def __init__(self, context):
        self.opened_files: dict[int, io.BytesIO] = dict()
        self._context = context
        self.next_fd = 1

    def __del__(self):
        self.close_all()

    def close_all(self):
        # Close all opened files
        self.opened_files.clear()
        self.next_fd = 0

    def open(self, filename: str, flags: int, mode: int):
        try:
            content = self._context.server_ifc.get_binary(filename)
            id = self.next_fd

            self.opened_files[id] = io.BytesIO(content)
            self.next_fd += 1
            return id
        except OSError as e:
            return f"-1,{e.errno}"

    def close(self, fd: int):
        if fd in self.opened_files.keys():
            del self.opened_files[fd]
            return True
        return False

    def pread(self, fd: int, count: int, offset: int):
        if fd in self.opened_files:
            stream = self.opened_files[fd]
            try:
                stream.seek(offset, os.SEEK_SET)
                return stream.read(count)
            except:
                return "-1, Exception while reading."
        else:
            return "-1"

    def pwrite(self, fd: int, offset: int, data: bytes):
        if fd in self.opened_files:
            stream = self.opened_files[fd]
            try:
                stream.seek(offset, os.SEEK_SET)
                return stream.write(data)
            except:
                return "-2,Error while writing."
        else:
            return "-1"
