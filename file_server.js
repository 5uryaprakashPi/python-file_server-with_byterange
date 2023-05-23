const http = require('http');
const fs = require('fs');
const path = require('path');

const server = http.createServer((req, res) => {
    // Get the requested file path
    const filePath = path.join(__dirname, req.url);

    // Check if the file exists
    fs.stat(filePath, (err, stats) => {
        if (err) {
            res.statusCode = 404;
            res.end('File or directory not found');
            return;
        }

        if (stats.isFile()) {
            // Set the appropriate Content-Type header for files
            const contentType = getContentType(filePath);
            res.setHeader('Content-Type', contentType);

            // Check if byte range requested
            const rangeHeader = req.headers.range;
            if (rangeHeader) {
                // Parse the byte range values
                const range = parseRangeHeader(rangeHeader, stats.size);

                // Check if the range is satisfiable
                if (range && range.start < range.end) {
                    // Set the appropriate Content-Range header
                    res.statusCode = 206;
                    res.setHeader('Content-Range', `bytes ${range.start}-${range.end}/${stats.size}`);
                    res.setHeader('Content-Length', range.end - range.start + 1);

                    // Read and stream the requested byte range
                    const fileStream = fs.createReadStream(filePath, { start: range.start, end: range.end });
                    fileStream.pipe(res);
                    return;
                }
            }

            // No byte range requested or range not satisfiable
            res.setHeader('Content-Length', stats.size);
            fs.createReadStream(filePath).pipe(res);
        } else if (stats.isDirectory()) {
            // Read the directory contents
            fs.readdir(filePath, (err, files) => {
                if (err) {
                    res.statusCode = 500;
                    res.end('Error reading directory');
                    return;
                }

                // Generate the directory listing HTML
                const directoryListing = generateDirectoryListing(req.url, files);

                // Set the Content-Type header to HTML
                res.setHeader('Content-Type', 'text/html');

                // Send the directory listing HTML as the response
                res.statusCode = 200;
                res.end(directoryListing);
            });
        }
    });
});

const port = 8000;
server.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});

function getContentType(filePath) {
    const extname = path.extname(filePath);
    switch (extname) {
        case '.html':
            return 'text/html';
        case '.css':
            return 'text/css';
        case '.js':
            return 'text/javascript';
        case '.json':
            return 'application/json';
        case '.png':
            return 'image/png';
        case '.jpg':
        case '.jpeg':
            return 'image/jpeg';
        case '.gif':
            return 'image/gif';
        case '.pdf':
            return 'application/pdf';
        case '.mp4':
            return 'video/mp4';
        default:
            return 'application/octet-stream';
    }
}

function parseRangeHeader(rangeHeader, fileSize) {
    const rangeRegex = /bytes=(\d+)-(\d*)/;
    const match = rangeRegex.exec(rangeHeader);
    if (match) {
        const start = parseInt(match[1]);
        const end = match[2] ? parseInt(match[2]) : fileSize - 1;
        return { start, end };
    }
    return null;
}

function generateDirectoryListing(url, files) {
    const formattedFiles = files.map((file) => {
        const fileUrl = path.join(url, file);
        const isDirectory = fs.statSync(path.join(__dirname, fileUrl)).isDirectory();
        const fileLink = isDirectory ? `${fileUrl}/` : fileUrl;
        return `<li><a href="${fileLink}">${file}</a></li>`;
    });
    const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Directory Listing</title>
      </head>
      <body>
        <h1>Directory Listing</h1>
        <ul>
          ${formattedFiles.join('\n')}
        </ul>
      </body>
    </html>
  `;
    return html;
}
