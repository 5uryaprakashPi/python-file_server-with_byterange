import http.server
import os
import mimetypes


class CustomFileHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Get the requested file path
        file_path = self.translate_path(self.path)

        # Check if the file exists
        if not os.path.exists(file_path):
            self.send_response(404)
            self.end_headers()
            return

        # Check if the path is a directory
        if os.path.isdir(file_path):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            # Generate the HTML for the directory listing
            html = "<html><body><ul>"
            for entry in os.scandir(file_path):
                entry_path = os.path.join(file_path, entry.name)
                if entry.is_dir():
                    html += f'<li><a href="{entry.name}/">{entry.name}/</a></li>'
                else:
                    html += f'<li><a href="{entry.name}">{entry.name}</a></li>'
            html += "</ul></body></html>"

            self.wfile.write(html.encode("utf-8"))
        else:
            # Get the file size
            file_size = os.path.getsize(file_path)

            # Parse the range header
            start_range, end_range = self.parse_range_header(file_size)

            if start_range is None or end_range is None:
                # Full file requested
                self.send_response(200)
                self.send_header("Content-Length", str(file_size))
                self.send_header(
                    "Content-Type", self.guess_mime_type(file_path))
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
                self.send_header(
                    "Content-Type", self.guess_mime_type(file_path))
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
httpd = http.server.HTTPServer(address, CustomFileHandler)
httpd.serve_forever()
