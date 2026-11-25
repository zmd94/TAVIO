"""Validation, processing, and safe atomic storage for the school logo PNG."""

from __future__ import annotations

import logging
import os
import tempfile
import warnings
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)

MAX_LOGO_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MIN_LOGO_DIMENSION = 128
MAX_LOGO_DIMENSION = 3000
SUPPORTED_IMAGE_FORMATS = frozenset({"PNG", "JPEG"})


class SchoolLogoError(RuntimeError):
    """Raised when a school logo fails validation, processing, or atomic storage."""


@dataclass(frozen=True, slots=True)
class ProcessedLogoInfo:
    """Metadata describing a validated and saved school logo PNG."""

    original_format: str
    original_size: tuple[int, int]
    final_size: tuple[int, int]
    was_resized: bool
    has_transparency: bool
    output_path: Path


def _has_image_transparency(image: Image.Image) -> bool:
    if image.mode in ("RGBA", "LA", "PA"):
        return True
    return "transparency" in image.info


def _calculate_proportional_size(width: int, height: int) -> tuple[int, int]:
    if width <= MAX_LOGO_DIMENSION and height <= MAX_LOGO_DIMENSION:
        return width, height
    if width >= height:
        new_width = MAX_LOGO_DIMENSION
        new_height = max(1, min(MAX_LOGO_DIMENSION, round(height * MAX_LOGO_DIMENSION / width)))
        return new_width, new_height
    new_height = MAX_LOGO_DIMENSION
    new_width = max(1, min(MAX_LOGO_DIMENSION, round(width * MAX_LOGO_DIMENSION / height)))
    return new_width, new_height


class SchoolLogoService:
    """Handles validation, proportional resizing, PNG conversion, and atomic replacement."""

    def process_and_save_logo(
        self,
        source_path: Path,
        destination_path: Path,
    ) -> ProcessedLogoInfo:
        """Validate ``source_path``, convert to lossless PNG, and atomically write ``destination_path``."""
        if not source_path.is_file():
            raise SchoolLogoError("The selected logo file does not exist.")

        try:
            file_size = source_path.stat().st_size
        except OSError as exc:
            raise SchoolLogoError(f"Unable to read logo file metadata: {exc}") from exc

        if file_size == 0:
            raise SchoolLogoError("The selected logo file is empty.")
        if file_size > MAX_LOGO_FILE_SIZE_BYTES:
            raise SchoolLogoError(
                "The selected logo file exceeds the 5 MB (5,242,880 bytes) size limit."
            )

        previous_truncated_flag = ImageFile.LOAD_TRUNCATED_IMAGES
        ImageFile.LOAD_TRUNCATED_IMAGES = False
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(source_path) as raw_image:
                    original_format = (raw_image.format or "").upper()
                    if original_format not in SUPPORTED_IMAGE_FORMATS:
                        raise SchoolLogoError(
                            "Unsupported image format. Please choose a valid PNG, JPG, or JPEG image."
                        )

                    # Decode full pixel stream so corrupted/truncated payloads fail here.
                    raw_image.load()
                    oriented = ImageOps.exif_transpose(raw_image)
                    orig_width, orig_height = oriented.size

                    if orig_width < MIN_LOGO_DIMENSION or orig_height < MIN_LOGO_DIMENSION:
                        raise SchoolLogoError(
                            f"Logo dimensions ({orig_width}x{orig_height} px) are too small. "
                            f"Minimum required size is {MIN_LOGO_DIMENSION}x{MIN_LOGO_DIMENSION} pixels."
                        )

                    has_transparency = _has_image_transparency(oriented)
                    if has_transparency:
                        working = oriented if oriented.mode == "RGBA" else oriented.convert("RGBA")
                    elif oriented.mode in ("RGB", "L"):
                        working = oriented.copy()
                    else:
                        working = oriented.convert("RGB")

                    target_width, target_height = _calculate_proportional_size(
                        orig_width,
                        orig_height,
                    )
                    was_resized = (target_width, target_height) != (orig_width, orig_height)
                    if was_resized:
                        working = working.resize(
                            (target_width, target_height),
                            Image.Resampling.LANCZOS,
                        )

                    self._write_png_atomically(working, destination_path)
        except SchoolLogoError:
            raise
        except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise SchoolLogoError(
                "The selected image exceeds safe pixel decoding limits and was rejected."
            ) from exc
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError, EOFError) as exc:
            raise SchoolLogoError(
                f"The selected file is corrupted or not a valid PNG/JPG/JPEG image: {exc}"
            ) from exc
        finally:
            ImageFile.LOAD_TRUNCATED_IMAGES = previous_truncated_flag

        logger.info(
            "Saved processed school logo to %s (%dx%d -> %dx%d, format=%s->PNG, alpha=%s)",
            destination_path,
            orig_width,
            orig_height,
            target_width,
            target_height,
            original_format,
            has_transparency,
        )
        return ProcessedLogoInfo(
            original_format=original_format,
            original_size=(orig_width, orig_height),
            final_size=(target_width, target_height),
            was_resized=was_resized,
            has_transparency=has_transparency,
            output_path=destination_path,
        )

    def _write_png_atomically(self, image: Image.Image, destination_path: Path) -> None:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination_path.parent,
                prefix=".school_logo_",
                suffix=".tmp.png",
                delete=False,
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)
                image.save(tmp_file, format="PNG", optimize=True)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())

            if not tmp_path.is_file() or tmp_path.stat().st_size == 0:
                raise SchoolLogoError("Processed PNG logo output was empty.")

            os.replace(tmp_path, destination_path)
            tmp_path = None
        except SchoolLogoError:
            raise
        except OSError as exc:
            raise SchoolLogoError(f"Failed to save processed logo file: {exc}") from exc
        finally:
            if tmp_path is not None:
                with suppress(OSError):
                    tmp_path.unlink(missing_ok=True)

    def remove_logo_file(self, logo_path: Path) -> bool:
        """Remove ``logo_path`` if present on disk. Return True if a file was deleted."""
        try:
            if not logo_path.exists():
                return False
            if logo_path.is_dir():
                raise SchoolLogoError(f"Expected logo file, found directory: {logo_path}")
            logo_path.unlink()
            return True
        except OSError as exc:
            raise SchoolLogoError(f"Failed to remove logo file '{logo_path}': {exc}") from exc
