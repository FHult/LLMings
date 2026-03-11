"""Unit tests for FileProcessor — the most security-sensitive service."""
import base64
import io
import pytest
from PIL import Image

from app.services.file_processor import FileProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_png(width: int = 10, height: int = 10) -> bytes:
    """Create a minimal valid PNG in memory."""
    img = Image.new("RGB", (width, height), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_jpeg(width: int = 10, height: int = 10) -> bytes:
    img = Image.new("RGB", (width, height), color=(0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Image processing
# ---------------------------------------------------------------------------

class TestImageProcessing:
    def test_valid_small_image_returns_base64(self):
        """A normal image produces a non-empty base64 string."""
        content = _make_png(20, 20)
        description, b64 = FileProcessor._process_image(content, ".png")
        assert b64 is not None
        # Must be decodeable base64
        decoded = base64.b64decode(b64)
        assert len(decoded) > 0
        assert "20x20" in description

    def test_image_description_contains_dimensions(self):
        content = _make_png(64, 32)
        description, _ = FileProcessor._process_image(content, ".png")
        assert "64x32" in description

    def test_oversized_image_rejected(self):
        """Images wider or taller than MAX_DIMENSION must be blocked before decoding."""
        # Create a large image
        oversized = _make_png(17000, 10)
        description, b64 = FileProcessor._process_image(oversized, ".png")
        assert b64 is None
        assert "too large" in description.lower()
        assert "17000" in description

    def test_oversized_height_rejected(self):
        oversized = _make_png(10, 17000)
        description, b64 = FileProcessor._process_image(oversized, ".png")
        assert b64 is None
        assert "too large" in description.lower()

    def test_image_at_exact_dimension_limit_accepted(self):
        """An image exactly at MAX_DIMENSION should be accepted."""
        limit = 16384
        at_limit = _make_png(limit, 1)
        description, b64 = FileProcessor._process_image(at_limit, ".png")
        assert b64 is not None
        assert "too large" not in description.lower()

    def test_corrupted_image_returns_error_string(self):
        """Corrupted bytes must not raise — returns an error description."""
        garbage = b"\x00\x01\x02corrupted image content"
        description, b64 = FileProcessor._process_image(garbage, ".jpg")
        assert b64 is None
        assert "error" in description.lower()

    def test_jpeg_returns_jpeg_base64(self):
        content = _make_jpeg(16, 16)
        description, b64 = FileProcessor._process_image(content, ".jpg")
        assert b64 is not None

    def test_rgba_image_converted_to_rgb(self):
        """RGBA images must not crash — converted before encoding."""
        img = Image.new("RGBA", (10, 10), color=(0, 0, 255, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        content = buf.getvalue()
        description, b64 = FileProcessor._process_image(content, ".png")
        assert b64 is not None


# ---------------------------------------------------------------------------
# Text and code file processing
# ---------------------------------------------------------------------------

class TestTextProcessing:
    def test_plain_text_decoded(self):
        content = b"Hello, world!"
        text, b64 = FileProcessor.process_file(content, "readme.txt")
        assert text == "Hello, world!"
        assert b64 is None

    def test_python_file_decoded(self):
        src = b"def hello():\n    return 'world'\n"
        text, b64 = FileProcessor.process_file(src, "script.py")
        assert "def hello" in text
        assert b64 is None

    def test_json_file_decoded(self):
        content = b'{"key": "value"}'
        text, b64 = FileProcessor.process_file(content, "data.json")
        assert '"key"' in text

    def test_csv_decoded(self):
        content = b"name,age\nAlice,30\nBob,25\n"
        text, b64 = FileProcessor.process_file(content, "data.csv")
        assert "Alice" in text
        assert b64 is None

    def test_markdown_decoded(self):
        content = b"# Title\n\nParagraph text."
        text, b64 = FileProcessor.process_file(content, "notes.md")
        assert "# Title" in text

    def test_utf8_with_non_ascii(self):
        content = "Héllo wörld – naïve café".encode("utf-8")
        text, b64 = FileProcessor.process_file(content, "unicode.txt")
        assert "Héllo" in text

    def test_invalid_utf8_does_not_crash(self):
        """Files with non-UTF8 bytes should not raise — errors='ignore' handles them."""
        content = b"valid\xff\xfeinvalid"
        text, _ = FileProcessor.process_file(content, "binary.txt")
        assert "valid" in text  # valid portion preserved

    def test_unsupported_extension_returns_placeholder(self):
        content = b"binary content"
        text, b64 = FileProcessor.process_file(content, "file.xyz")
        assert "Unsupported" in text
        assert b64 is None


# ---------------------------------------------------------------------------
# File type detection
# ---------------------------------------------------------------------------

class TestFileTypeDetection:
    @pytest.mark.parametrize("filename", [
        "doc.pdf", "img.jpg", "img.jpeg", "img.png", "img.gif", "img.bmp",
        "img.webp", "sheet.xlsx", "data.csv", "code.py", "code.js",
        "code.ts", "code.go", "code.rs", "code.java", "script.sh",
        "query.sql", "notes.md", "notes.txt",
    ])
    def test_supported_extensions(self, filename):
        assert FileProcessor.is_supported(filename) is True

    @pytest.mark.parametrize("filename", [
        "file.exe", "archive.zip", "binary.bin", "movie.mp4", "unknown.xyz",
    ])
    def test_unsupported_extensions(self, filename):
        assert FileProcessor.is_supported(filename) is False

    @pytest.mark.parametrize("filename", [
        "photo.jpg", "photo.jpeg", "photo.png", "photo.gif",
        "photo.bmp", "photo.webp",
    ])
    def test_image_extensions_detected(self, filename):
        assert FileProcessor.is_image(filename) is True

    def test_pdf_is_not_image(self):
        assert FileProcessor.is_image("doc.pdf") is False

    def test_py_is_not_image(self):
        assert FileProcessor.is_image("script.py") is False

    def test_case_insensitive(self):
        """Extension detection must be case-insensitive."""
        assert FileProcessor.is_supported("PHOTO.PNG") is True
        assert FileProcessor.is_image("PHOTO.PNG") is True

    def test_no_extension_not_supported(self):
        assert FileProcessor.is_supported("Makefile") is False
