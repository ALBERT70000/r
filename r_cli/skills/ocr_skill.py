"""
Skill de OCR para R CLI.

Extrae texto de:
- Imágenes (PNG, JPG, etc.)
- PDFs escaneados
- Capturas de pantalla
- Documentos fotografiados

Usa Tesseract OCR (open source, offline).
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from r_cli.core.agent import Skill
from r_cli.core.llm import Tool


class OCRSkill(Skill):
    """Skill para extracción de texto con OCR."""

    name = "ocr"
    description = "Extrae texto de imágenes y PDFs escaneados usando Tesseract OCR"

    # Idiomas soportados por Tesseract
    LANGUAGES = {
        "eng": "English",
        "spa": "Spanish",
        "fra": "French",
        "deu": "German",
        "ita": "Italian",
        "por": "Portuguese",
        "chi_sim": "Chinese (Simplified)",
        "chi_tra": "Chinese (Traditional)",
        "jpn": "Japanese",
        "kor": "Korean",
        "ara": "Arabic",
        "rus": "Russian",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Verifica si Tesseract está instalado."""
        return shutil.which("tesseract") is not None

    def _check_poppler(self) -> bool:
        """Verifica si Poppler (pdftoppm) está instalado para PDFs."""
        return shutil.which("pdftoppm") is not None

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="extract_text_from_image",
                description="Extrae texto de una imagen usando OCR",
                parameters={
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Ruta a la imagen (PNG, JPG, TIFF, etc.)",
                        },
                        "language": {
                            "type": "string",
                            "description": "Idioma del texto (eng, spa, fra, deu, etc.)",
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Ruta para guardar el texto extraído (opcional)",
                        },
                    },
                    "required": ["image_path"],
                },
                handler=self.extract_from_image,
            ),
            Tool(
                name="extract_text_from_pdf",
                description="Extrae texto de un PDF (incluyendo escaneados)",
                parameters={
                    "type": "object",
                    "properties": {
                        "pdf_path": {
                            "type": "string",
                            "description": "Ruta al archivo PDF",
                        },
                        "language": {
                            "type": "string",
                            "description": "Idioma del texto (eng, spa, fra, etc.)",
                        },
                        "pages": {
                            "type": "string",
                            "description": "Páginas a procesar (ej: '1-5', 'all')",
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Ruta para guardar el texto extraído",
                        },
                    },
                    "required": ["pdf_path"],
                },
                handler=self.extract_from_pdf,
            ),
            Tool(
                name="ocr_to_searchable_pdf",
                description="Convierte un PDF escaneado a PDF con texto seleccionable",
                parameters={
                    "type": "object",
                    "properties": {
                        "pdf_path": {
                            "type": "string",
                            "description": "Ruta al PDF escaneado",
                        },
                        "language": {
                            "type": "string",
                            "description": "Idioma del texto",
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Ruta para el PDF de salida",
                        },
                    },
                    "required": ["pdf_path"],
                },
                handler=self.create_searchable_pdf,
            ),
            Tool(
                name="batch_ocr",
                description="Procesa múltiples imágenes en un directorio",
                parameters={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directorio con imágenes",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Patrón de archivos (ej: *.png, *.jpg)",
                        },
                        "language": {
                            "type": "string",
                            "description": "Idioma del texto",
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Archivo donde concatenar todo el texto",
                        },
                    },
                    "required": ["directory"],
                },
                handler=self.batch_ocr,
            ),
            Tool(
                name="list_ocr_languages",
                description="Lista los idiomas disponibles para OCR",
                parameters={"type": "object", "properties": {}},
                handler=self.list_languages,
            ),
        ]

    def extract_from_image(
        self,
        image_path: str,
        language: str = "eng",
        output_file: Optional[str] = None,
    ) -> str:
        """Extrae texto de una imagen."""
        if not self._tesseract_available:
            return self._install_instructions()

        try:
            path = Path(image_path)

            if not path.exists():
                return f"Error: Imagen no encontrada: {image_path}"

            # Verificar formato
            valid_extensions = [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"]
            if path.suffix.lower() not in valid_extensions:
                return f"Error: Formato no soportado. Use: {', '.join(valid_extensions)}"

            # Ejecutar Tesseract
            result = subprocess.run(
                [
                    "tesseract",
                    str(path),
                    "stdout",
                    "-l",
                    language,
                    "--psm",
                    "3",  # Automatic page segmentation
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                error = result.stderr or "Error desconocido"
                if "Tesseract couldn't load any languages" in error:
                    return f"Error: Idioma '{language}' no instalado. Ejecuta: brew install tesseract-lang"
                return f"Error en OCR: {error}"

            text = result.stdout.strip()

            if not text:
                return "No se detectó texto en la imagen."

            # Guardar a archivo si se especifica
            if output_file:
                out_path = Path(output_file)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(text)
                return f"Texto extraido y guardado en: {out_path}\n\n{text[:1000]}{'...' if len(text) > 1000 else ''}"

            return f"Texto extraido ({len(text)} caracteres):\n\n{text}"

        except subprocess.TimeoutExpired:
            return "Error: Timeout procesando imagen (>120s)"
        except Exception as e:
            return f"Error en OCR: {e}"

    def extract_from_pdf(
        self,
        pdf_path: str,
        language: str = "eng",
        pages: str = "all",
        output_file: Optional[str] = None,
    ) -> str:
        """Extrae texto de un PDF."""
        if not self._tesseract_available:
            return self._install_instructions()

        try:
            path = Path(pdf_path)

            if not path.exists():
                return f"Error: PDF no encontrado: {pdf_path}"

            # Primero intentar extracción directa (para PDFs con texto)
            direct_text = self._extract_pdf_text_direct(path)
            if direct_text and len(direct_text.strip()) > 100:
                if output_file:
                    Path(output_file).write_text(direct_text)
                    return f"Texto extraido directamente y guardado en: {output_file}"
                return f"Texto extraido directamente ({len(direct_text)} chars):\n\n{direct_text[:2000]}..."

            # Si no hay texto, usar OCR
            if not self._check_poppler():
                return "Error: Poppler no instalado. Necesario para PDFs escaneados.\nInstala: brew install poppler"

            all_text = []

            with tempfile.TemporaryDirectory() as tmpdir:
                # Convertir PDF a imágenes
                subprocess.run(
                    [
                        "pdftoppm",
                        "-png",
                        "-r",
                        "300",  # 300 DPI para mejor OCR
                        str(path),
                        f"{tmpdir}/page",
                    ],
                    check=False,
                    capture_output=True,
                    timeout=300,
                )

                # Procesar cada página
                page_images = sorted(Path(tmpdir).glob("page-*.png"))

                if not page_images:
                    return "Error: No se pudieron extraer páginas del PDF"

                for i, img_path in enumerate(page_images, 1):
                    result = subprocess.run(
                        [
                            "tesseract",
                            str(img_path),
                            "stdout",
                            "-l",
                            language,
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )

                    if result.stdout.strip():
                        all_text.append(f"--- Pagina {i} ---\n{result.stdout.strip()}")

            if not all_text:
                return "No se detectó texto en el PDF."

            full_text = "\n\n".join(all_text)

            if output_file:
                Path(output_file).write_text(full_text)
                return (
                    f"Texto OCR extraido de {len(page_images)} paginas. Guardado en: {output_file}"
                )

            return f"Texto OCR ({len(page_images)} paginas, {len(full_text)} chars):\n\n{full_text[:3000]}..."

        except subprocess.TimeoutExpired:
            return "Error: Timeout procesando PDF"
        except Exception as e:
            return f"Error procesando PDF: {e}"

    def _extract_pdf_text_direct(self, pdf_path: Path) -> str:
        """Intenta extraer texto directamente del PDF (sin OCR)."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(pdf_path))
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)
        except Exception:
            return ""

    def create_searchable_pdf(
        self,
        pdf_path: str,
        language: str = "eng",
        output_path: Optional[str] = None,
    ) -> str:
        """Crea un PDF con capa de texto seleccionable."""
        if not self._tesseract_available:
            return self._install_instructions()

        try:
            path = Path(pdf_path)

            if not path.exists():
                return f"Error: PDF no encontrado: {pdf_path}"

            # Determinar salida
            if output_path:
                out_path = Path(output_path)
            else:
                out_path = path.with_stem(f"{path.stem}_searchable")

            # Usar Tesseract para crear PDF con OCR
            with tempfile.TemporaryDirectory() as tmpdir:
                # Convertir a imágenes primero
                subprocess.run(
                    ["pdftoppm", "-png", "-r", "300", str(path), f"{tmpdir}/page"],
                    check=False,
                    capture_output=True,
                    timeout=300,
                )

                page_images = sorted(Path(tmpdir).glob("page-*.png"))

                if not page_images:
                    return "Error: No se pudieron extraer páginas"

                # Crear PDF con OCR para cada página
                pdf_parts = []
                for img in page_images:
                    pdf_out = img.with_suffix("")
                    subprocess.run(
                        [
                            "tesseract",
                            str(img),
                            str(pdf_out),
                            "-l",
                            language,
                            "pdf",
                        ],
                        check=False,
                        capture_output=True,
                        timeout=60,
                    )
                    pdf_parts.append(f"{pdf_out}.pdf")

                # Unir PDFs si hay múltiples
                if len(pdf_parts) == 1:
                    shutil.copy(pdf_parts[0], out_path)
                # Usar pdfunite si está disponible
                elif shutil.which("pdfunite"):
                    subprocess.run(
                        ["pdfunite"] + pdf_parts + [str(out_path)],
                        check=False,
                        capture_output=True,
                    )
                else:
                    # Fallback: solo copiar primera página
                    shutil.copy(pdf_parts[0], out_path)
                    return f"PDF searchable creado (solo primera pagina, instala poppler-utils para unir): {out_path}"

            return f"PDF searchable creado: {out_path}"

        except Exception as e:
            return f"Error creando PDF searchable: {e}"

    def batch_ocr(
        self,
        directory: str,
        pattern: str = "*.png",
        language: str = "eng",
        output_file: Optional[str] = None,
    ) -> str:
        """Procesa múltiples imágenes."""
        if not self._tesseract_available:
            return self._install_instructions()

        try:
            dir_path = Path(directory)

            if not dir_path.exists():
                return f"Error: Directorio no encontrado: {directory}"

            images = list(dir_path.glob(pattern))

            if not images:
                return f"No se encontraron imagenes con patron '{pattern}' en {directory}"

            all_text = []
            processed = 0
            errors = 0

            for img_path in sorted(images):
                result = subprocess.run(
                    [
                        "tesseract",
                        str(img_path),
                        "stdout",
                        "-l",
                        language,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0 and result.stdout.strip():
                    all_text.append(f"--- {img_path.name} ---\n{result.stdout.strip()}")
                    processed += 1
                else:
                    errors += 1

            if not all_text:
                return f"No se extrajo texto de ninguna imagen ({errors} errores)"

            full_text = "\n\n".join(all_text)

            if output_file:
                Path(output_file).write_text(full_text)
                return f"Procesadas {processed} imagenes ({errors} errores). Texto guardado en: {output_file}"

            return f"Procesadas {processed} imagenes ({errors} errores):\n\n{full_text[:3000]}..."

        except Exception as e:
            return f"Error en batch OCR: {e}"

    def list_languages(self) -> str:
        """Lista idiomas disponibles."""
        result = ["Idiomas soportados por Tesseract OCR:\n"]

        for code, name in self.LANGUAGES.items():
            result.append(f"  - {code}: {name}")

        result.append("\nNota: Algunos idiomas requieren instalación adicional.")
        result.append("macOS: brew install tesseract-lang")
        result.append("Ubuntu: apt install tesseract-ocr-[lang]")

        # Verificar idiomas instalados
        if self._tesseract_available:
            try:
                installed = subprocess.run(
                    ["tesseract", "--list-langs"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if installed.returncode == 0:
                    langs = installed.stdout.strip().split("\n")[1:]  # Skip header
                    result.append(f"\nInstalados en este sistema: {', '.join(langs)}")
            except Exception:
                pass

        return "\n".join(result)

    def _install_instructions(self) -> str:
        """Instrucciones de instalación de Tesseract."""
        return """Error: Tesseract OCR no está instalado.

Instrucciones de instalación:

macOS:
  brew install tesseract
  brew install tesseract-lang  # Para más idiomas

Ubuntu/Debian:
  sudo apt install tesseract-ocr
  sudo apt install tesseract-ocr-spa  # Español

Windows:
  Descarga de: https://github.com/UB-Mannheim/tesseract/wiki
"""

    def execute(self, **kwargs) -> str:
        """Ejecución directa del skill."""
        image = kwargs.get("image")
        pdf = kwargs.get("pdf")
        language = kwargs.get("language", "eng")

        if image:
            return self.extract_from_image(image, language, kwargs.get("output"))
        elif pdf:
            return self.extract_from_pdf(pdf, language, output_file=kwargs.get("output"))
        else:
            return "Error: Se requiere una imagen o PDF para OCR"
