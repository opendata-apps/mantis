import logging

import svgwrite

logger = logging.getLogger(__name__)


def create_measure_sheet(
    row_range=(24, 46),
    col_range=(33, 54),
    box_size=50,
    dataset=None,
    bg_image_url=None,
):
    """Render an MTB grid SVG and return it as a string.

    ``bg_image_url`` is optional; when provided it is referenced by an ``<image>``
    element. Keeping this as a parameter (rather than calling ``url_for`` here)
    decouples rendering from a Flask request context.
    """
    logger.debug("dataset = %s", dataset)
    # MTB number = RRCC, rows go N->S (vertical axis), cols go W->E (horizontal axis).
    width = (col_range[1] - col_range[0] + 2) * box_size
    height = (row_range[1] - row_range[0] + 2) * box_size

    dwg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))

    if bg_image_url:
        bg_size = (width - box_size * 1.2, height - box_size * 2)
        bg_insert = (box_size * 1.3, box_size * 1.2)
        bg_center = (bg_insert[0] + bg_size[0] / 2, bg_insert[1] + bg_size[1] / 2)
        dwg.add(
            dwg.image(
                href=bg_image_url,
                insert=bg_insert,
                size=bg_size,
                transform="rotate(3, {0}, {1})".format(bg_center[0], bg_center[1]),
            )
        )

    # Zeichnen der horizontalen Linien und Beschriften (eine pro Zeilengrenze)
    for i in range(row_range[0], row_range[1] + 2):
        y_coord = (i - row_range[0] + 1) * box_size
        dwg.add(
            dwg.line(
                start=(box_size, y_coord),
                end=(width, y_coord),
                stroke=svgwrite.rgb(0, 0, 0, "%"),
                stroke_width=0.2,
            )
        )
        dwg.add(
            dwg.text(
                f"{i}",
                insert=((box_size / 1.5), y_coord + box_size // 2),
                fill="black",
                text_anchor="end",
                font_size=(box_size / 3),
            )
        )

    # Zeichnen der vertikalen Linien und Beschriften (eine pro Spaltengrenze)
    for j in range(col_range[0], col_range[1] + 2):
        x_coord = (j - col_range[0] + 1) * box_size
        dwg.add(
            dwg.line(
                start=(x_coord, box_size),
                end=(x_coord, height),
                stroke=svgwrite.rgb(0, 0, 0, "%"),
                stroke_width=0.2,
            )
        )
        dwg.add(
            dwg.text(
                f"{j}",
                insert=(x_coord + box_size // 2, box_size // 2),
                fill="black",
                text_anchor="middle",
                font_size=(box_size / 3),
            )
        )

    # Zeichnen der Kreiszeichen und Beschriften basierend auf dbanswer
    if dataset is not None:
        for coord, count in dataset:
            col = coord % 100
            row = coord // 100
            if not (
                row_range[0] <= row <= row_range[1]
                and col_range[0] <= col <= col_range[1]
            ):
                logger.warning(
                    "Skipping MTB %s: outside grid (rows %s, cols %s)",
                    coord,
                    row_range,
                    col_range,
                )
                continue
            distance_from_start_x = col - col_range[0]
            distance_from_start_y = row - row_range[0]
            circle_center = (
                distance_from_start_x * box_size + (box_size * 1.5),
                distance_from_start_y * box_size + (box_size * 1.5),
            )
            dwg.add(dwg.circle(center=circle_center, r=box_size // 3, fill="black"))
            dwg.add(
                dwg.text(
                    f"{count}",
                    insert=circle_center,
                    fill="white",
                    dominant_baseline="middle",
                    text_anchor="middle",
                    font_size=(box_size / 3),
                    dy="1",
                )
            )

    # Speichern der SVG-Datei
    # dwg.save()
    # Ausgabe als Text
    return dwg.tostring()


if __name__ == "__main__":
    # Bereich des Messtischblatts
    # Zeilen (rows, vertikal): 24-46
    # Spalten (cols, horizontal): 33-54
    rows = (24, 46)
    cols = (33, 54)

    box_size = 50

    dbanswer = [(3328, 5), (3830, 10), (4138, 1), (5446, 3), (4634, 99)]

    print(create_measure_sheet(rows, cols, box_size, dataset=dbanswer))
