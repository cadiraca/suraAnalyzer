"""
PDF Tools API Router.

Provides endpoints for PDF manipulation:
- compress: reduce file size by downscaling embedded images
- split: divide a PDF into smaller chunks by page count
"""

import io
import logging
import os
import tempfile
import zipfile

from fastapi import APIRouter, HTTPException, UploadFile, Form
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

pdf_tools_router = APIRouter(prefix="/api/v1/pdf-tools", tags=["PDF Tools"])


def _require_fitz():
    """Import PyMuPDF (fitz) and raise a clear error if not installed."""
    try:
        import fitz  # PyMuPDF
        return fitz
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail=(
                "PyMuPDF is not installed. "
                "Add 'PyMuPDF>=1.24.0' to requirements.txt and reinstall."
            ),
        )


# ---------------------------------------------------------------------------
# POST /api/v1/pdf-tools/compress
# ---------------------------------------------------------------------------

@pdf_tools_router.post("/compress")
async def compress_pdf(
    file: UploadFile,
    quality: int = Form(default=72, ge=1, le=95),
):
    """
    Compress a PDF by re-encoding embedded images at a lower JPEG quality.

    - **file**: PDF file to compress
    - **quality**: JPEG quality for embedded images (1–95, default 72)

    Returns the compressed PDF as a file download.
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        # Accept if extension is .pdf even when content_type is generic
        filename = file.filename or ""
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are accepted.",
            )

    fitz = _require_fitz()

    # Read uploaded bytes
    pdf_bytes = await file.read()
    original_size = len(pdf_bytes)
    logger.info(
        "compress_pdf: received '%s' (%d bytes), quality=%d",
        file.filename,
        original_size,
        quality,
    )

    # Process in a temp file so fitz can handle large docs
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_in:
        tmp_in.write(pdf_bytes)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path + "_compressed.pdf"

    try:
        doc = fitz.open(tmp_in_path)
        for page in doc:
            # Iterate over all image references on the page
            for img_ref in page.get_images(full=True):
                xref = img_ref[0]
                try:
                    # Extract image as a Pixmap and re-encode at target quality
                    pix = fitz.Pixmap(doc, xref)

                    # Convert CMYK / alpha to RGB for JPEG encoding
                    if pix.n > 4:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    elif pix.alpha:
                        pix = fitz.Pixmap(pix, 0)  # drop alpha

                    # Re-encode as JPEG at the requested quality
                    jpeg_bytes = pix.tobytes(output="jpeg", jpg_quality=quality)

                    # Replace the image stream in the document
                    doc.update_stream(xref, jpeg_bytes)
                except Exception as img_err:
                    # If a single image fails, log and continue
                    logger.warning("Could not compress image xref=%d: %s", xref, img_err)

        # Save with garbage collection and deflate compression
        doc.save(
            tmp_out_path,
            garbage=4,
            deflate=True,
            clean=True,
        )
        doc.close()

        with open(tmp_out_path, "rb") as f:
            compressed_bytes = f.read()

    finally:
        # Cleanup temp files
        for path in (tmp_in_path, tmp_out_path):
            try:
                os.unlink(path)
            except OSError:
                pass

    compressed_size = len(compressed_bytes)
    logger.info(
        "compress_pdf: compressed '%s' from %d → %d bytes (%.1f%%)",
        file.filename,
        original_size,
        compressed_size,
        (1 - compressed_size / original_size) * 100 if original_size else 0,
    )

    original_name = os.path.splitext(file.filename or "documento")[0]
    download_name = f"compressed_{original_name}.pdf"

    return StreamingResponse(
        io.BytesIO(compressed_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "X-Original-Size": str(original_size),
            "X-Compressed-Size": str(compressed_size),
        },
    )


# ---------------------------------------------------------------------------
# POST /api/v1/pdf-tools/split
# ---------------------------------------------------------------------------

@pdf_tools_router.post("/split")
async def split_pdf(
    file: UploadFile,
    pages_per_chunk: int = Form(default=1000, ge=1, le=1000),
):
    """
    Split a PDF into multiple chunks of *pages_per_chunk* pages each.

    - **file**: PDF file to split
    - **pages_per_chunk**: number of pages per output file (1–1000, default 1000)

    Returns a ZIP archive containing all chunk PDFs.
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        filename = file.filename or ""
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are accepted.",
            )

    fitz = _require_fitz()

    pdf_bytes = await file.read()
    logger.info(
        "split_pdf: received '%s' (%d bytes), pages_per_chunk=%d",
        file.filename,
        len(pdf_bytes),
        pages_per_chunk,
    )

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_in:
        tmp_in.write(pdf_bytes)
        tmp_in_path = tmp_in.name

    zip_buffer = io.BytesIO()
    original_name = os.path.splitext(file.filename or "documento")[0]

    try:
        src = fitz.open(tmp_in_path)
        total_pages = src.page_count

        if total_pages == 0:
            raise HTTPException(status_code=400, detail="The PDF has no pages.")

        chunk_number = 1
        start = 0

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            while start < total_pages:
                end = min(start + pages_per_chunk, total_pages)  # exclusive upper bound

                chunk_doc = fitz.open()  # new empty document
                chunk_doc.insert_pdf(src, from_page=start, to_page=end - 1)

                chunk_name = f"{original_name}_part{chunk_number}.pdf"

                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_chunk:
                    tmp_chunk_path = tmp_chunk.name

                try:
                    chunk_doc.save(tmp_chunk_path, garbage=4, deflate=True)
                    chunk_doc.close()

                    with open(tmp_chunk_path, "rb") as f:
                        zf.writestr(chunk_name, f.read())

                    logger.info(
                        "split_pdf: chunk %d — pages %d–%d → '%s'",
                        chunk_number,
                        start + 1,
                        end,
                        chunk_name,
                    )
                finally:
                    try:
                        os.unlink(tmp_chunk_path)
                    except OSError:
                        pass

                start = end
                chunk_number += 1

        src.close()

    finally:
        try:
            os.unlink(tmp_in_path)
        except OSError:
            pass

    zip_buffer.seek(0)
    download_name = f"split_{original_name}.zip"

    logger.info(
        "split_pdf: created ZIP '%s' with %d chunks",
        download_name,
        chunk_number - 1,
    )

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
        },
    )
