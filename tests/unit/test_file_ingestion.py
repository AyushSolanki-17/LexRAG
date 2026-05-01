from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from lexrag.ingestion.file_ingestion import (
    FileIngestionGateway,
    FileTypeDetector,
    FileValidationService,
)


def test_validation_rejects_encrypted_pdf_header(tmp_path: Path) -> None:
    pdf_path = tmp_path / "encrypted.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n1 0 obj\n<< /Encrypt 2 0 R >>\n")

    result = FileValidationService().validate(pdf_path)

    assert result.encrypted is True
    assert result.is_valid is False
    assert result.failure_reason == "encrypted_pdf"


def test_gateway_marks_batch_duplicates_by_sha256(tmp_path: Path) -> None:
    first = tmp_path / "contract_a.txt"
    second = tmp_path / "contract_b.txt"
    first.write_text("same content", encoding="utf-8")
    second.write_text("same content", encoding="utf-8")

    reports = FileIngestionGateway().inspect_batch([first, second])

    assert reports[0].validation.duplicate_in_batch is False
    assert reports[1].validation.duplicate_in_batch is True
    assert reports[0].validation.sha256 == reports[1].validation.sha256


@pytest.mark.parametrize(
    ("name", "payload", "expected_family", "expected_media_type"),
    [
        (
            "page.html",
            b"<!doctype html><html><body>hello</body></html>",
            "html",
            "text/html",
        ),
        ("note.txt", b"plain text body", "text", "text/plain"),
        ("scan.png", b"\x89PNG\r\n\x1a\nrest", "image", "image/png"),
        (
            "mail.eml",
            b"Subject: Test\nMIME-Version: 1.0\n\nBody",
            "email",
            "message/rfc822",
        ),
    ],
)
def test_file_type_detector_classifies_supported_families(
    tmp_path: Path,
    name: str,
    payload: bytes,
    expected_family: str,
    expected_media_type: str,
) -> None:
    path = tmp_path / name
    path.write_bytes(payload)

    detection = FileTypeDetector().detect(path)

    assert detection.document_family == expected_family
    assert detection.detected_type == expected_family
    assert detection.media_type == expected_media_type


def test_validation_flags_corrupt_office_archive(tmp_path: Path) -> None:
    docx_path = tmp_path / "broken.docx"
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr("word/document.xml", "<w:document/>")

    result = FileValidationService().validate(docx_path)

    assert result.corrupted is True
    assert result.failure_reason == "corrupt_file"


def test_validation_blocks_when_no_antivirus_is_configured_in_prod(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "contract.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\n")
    monkeypatch.setenv("LEXRAG_ENV", "PROD")

    result = FileValidationService().validate(pdf_path)

    assert result.antivirus.status == "skipped"
    assert result.antivirus.blocking is True
    assert result.failure_reason == "antivirus_infected"
