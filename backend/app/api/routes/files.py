"""File upload API routes."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.file_processor import FileProcessor
from app.schemas.session import FileAttachment
from app.core.validation import MAX_FILE_SIZE, MAX_FILE_SIZE_MB

router = APIRouter()


@router.post("/files/upload", response_model=FileAttachment)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a file.

    Args:
        file: The uploaded file

    Returns:
        FileAttachment: Processed file information with extracted content
    """
    # Read file content
    content = await file.read()
    file_size = len(content)

    # Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"
        )

    # Check if file type is supported
    if not FileProcessor.is_supported(file.filename):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Supported types: {', '.join(sorted(FileProcessor.SUPPORTED_EXTENSIONS))}"
        )

    # Process the file
    try:
        extracted_text, base64_data = await FileProcessor.process_file(content, file.filename)

        return FileAttachment(
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            size=file_size,
            extracted_text=extracted_text,
            base64_data=base64_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/files/supported-types")
async def get_supported_types():
    """Get list of supported file types."""
    return {
        "extensions": sorted(list(FileProcessor.SUPPORTED_EXTENSIONS)),
        "image_extensions": sorted(list(FileProcessor.IMAGE_EXTENSIONS)),
        "categories": {
            "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
            "documents": [".pdf", ".txt", ".md", ".docx"],
            "code": [".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".c", ".cs",
                    ".go", ".rs", ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".sh", ".sql"],
            "spreadsheets": [".xlsx", ".csv"],
            "presentations": [".pptx"],
        }
    }
