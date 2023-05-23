import http.server
import os
import mimetypes


class ByteRangeFileHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Get the requested file path
        file_path = self.translate_path(self.path)

        # Check if the file exists
        if not os.path.isfile(file_path):
            self.send_response(404)
            self.end_headers()
            return

        # Get the file size
        file_size = os.path.getsize(file_path)

        # Parse the range header
        start_range, end_range = self.parse_range_header(file_size)

        if start_range is None or end_range is None:
            # Full file requested
            self.send_response(200)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Content-Type", self.guess_mime_type(file_path))
            self.end_headers()

            with open(file_path, "rb") as file:
                self.wfile.write(file.read())
        else:
            # Partial content requested
            self.send_response(206)
            self.send_header(
                "Content-Range", f"bytes {start_range}-{end_range}/{file_size}")
            self.send_header("Content-Length",
                             str(end_range - start_range + 1))
            self.send_header("Content-Type", self.guess_mime_type(file_path))
            self.end_headers()

            with open(file_path, "rb") as file:
                file.seek(start_range)
                self.wfile.write(file.read(end_range - start_range + 1))

    def parse_range_header(self, file_size):
        range_header = self.headers.get("Range")

        if range_header is None:
            return None, None

        # Parse the range header value
        start_range, end_range = range_header.strip().replace("bytes=", "").split("-")
        start_range = int(start_range) if start_range else 0
        end_range = int(end_range) if end_range else file_size - 1

        return start_range, end_range

    def guess_mime_type(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type if mime_type else "application/octet-stream"


# Start the server
address = ("", 8000)
httpd = http.server.HTTPServer(address, ByteRangeFileHandler)
httpd.serve_forever()
# ffmpeg -i "./DVD-2.mpg" -acodec copy -vcodec copy -f mp4 "./DVD-2.mp4"
