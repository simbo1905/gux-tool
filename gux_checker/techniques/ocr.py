"""OCR text extraction with positions and confidence scores.

Runs pytesseract.image_to_data() on each zone crop. Filters results
by confidence > 40. Outputs list of {text, x, y, w, h, confidence}
per zone.

Requires system tesseract-ocr package. If not installed, reports a
clear error without crashing.

Example:
    uv run gux-tool ocr ./tmp screenshot.png --gux dashboard.gux
"""

from gux_checker.core.types import Report, Technique, ZoneImage

technique = Technique(
    name='ocr',
    help='OCR each zone. Extract text, bounding boxes, confidence scores.',
)


@technique.run
def run(zones: list[ZoneImage], report: Report, args) -> None:
    try:
        import pytesseract
    except ImportError:
        for zone in zones:
            report.add(zone.name, 'ocr', {'error': 'pytesseract not installed'})
        return

    for zone in zones:
        try:
            data = pytesseract.image_to_data(zone.image, output_type=pytesseract.Output.DICT)
        except Exception as e:
            report.add(zone.name, 'ocr', {'error': f'tesseract failed: {e}'})
            continue

        texts = []
        detail = []
        n = len(data['text'])
        for i in range(n):
            conf = int(data['conf'][i]) if data['conf'][i] != '-1' else -1
            text = data['text'][i].strip()
            if conf > 40 and text:
                texts.append(text)
                detail.append(
                    {
                        'text': text,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'w': data['width'][i],
                        'h': data['height'][i],
                        'confidence': conf,
                    }
                )

        report.add(zone.name, 'ocr', {'texts': texts, 'detail': detail})
