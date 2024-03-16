import os
import svgwrite
from flask import url_for
#basedir = os.path.abspath(os.path.dirname(__file__))
#background = os.path.join(basedir, 'static/images/land_brandenburg.svg')

def create_measure_sheet(horizontal_range=(24, 46),
                         vertical_range=(33, 54),
                         box_size=50,
                         dataset=None):
    vertical_size = (24,46)
    horizontal_size = (33, 54)
    # Breite und Höhe der SVG-Datei
    width = (horizontal_range[1] - horizontal_range[0] + 1) * box_size
    height = (vertical_range[1] - vertical_range[0] + 3) * box_size
    
    # Erstellen der SVG-Zeichenfläche
    dwg = svgwrite.Drawing(filename="measure_sheet.svg",
                           size=(f"{width}px", f"{height}px"))
    # Pfad zur vorhandenen SVG-Datei mit dem Brandenburg-Bild
    
    bg_image = url_for('static', filename='images/land_brandenburg.svg')
    bg_size = (width - box_size*1.2, height - box_size*2)
    bg_insert = (box_size * 1.3, box_size * 1.2)
    # Mittelpunkt des Hintergrundbildes
    bg_center = (bg_insert[0] + bg_size[0] / 2, bg_insert[1] + bg_size[1] / 2)  
    dwg.add(dwg.image(href=bg_image, insert=bg_insert,
                      size=bg_size,
                      transform="rotate(3, {0}, {1})".format(bg_center[0],
                                                             bg_center[1])))
    
    # Zeichnen der horizontalen Linien und Beschriften
    for i in range(horizontal_range[0], horizontal_range[1] + 2):
        y_coord = (i - horizontal_range[0] + 1) * box_size
        dwg.add(dwg.line(start=(box_size, y_coord),
                         end=(width, y_coord),
                         stroke=svgwrite.rgb(0, 0, 0, '%'),
                         stroke_width=0.2))
        dwg.add(dwg.text(f"{i}", insert=((box_size/1.5),
                                         y_coord + box_size // 2),
                         fill='black',
                         text_anchor='end',
                         font_size=(box_size/3)))

    # Zeichnen der vertikalen Linien und Beschriften
    for j in range(vertical_range[0], vertical_range[1] + 2):
        x_coord = (j - vertical_range[0] + 1) * box_size
        dwg.add(dwg.line(start=(x_coord, box_size),
                         end=(x_coord, height),
                         stroke=svgwrite.rgb(0, 0, 0, '%'),
                         stroke_width=0.2))
        dwg.add(dwg.text(f"{j}", insert=(x_coord + box_size // 2,
                                         box_size // 2), fill='black',
                         text_anchor='middle', font_size=(box_size/3)))
    
    # Zeichnen der Kreiszeichen und Beschriften basierend auf dbanswer
    for coord, count in dataset:
        x_coord = (coord % 100)
        y_coord = (coord // 100)
        vertical_offset = 1
        distance_from_start_x = abs(x_coord - horizontal_size[0])
        distance_from_start_y = abs(y_coord - vertical_size[0])
        circle_center = (distance_from_start_x * box_size + (box_size * 1.5),
                         distance_from_start_y * box_size + (box_size * 1.5))
        dwg.add(dwg.circle(center=circle_center, r=box_size // 3, fill='black'))
        dwg.add(dwg.text(f"{count}", insert=circle_center,
                         fill='white',dominant_baseline='middle',
                         text_anchor='middle',
                         font_size=(box_size/3),
                         dy=f"{vertical_offset}"))
    
    # Speichern der SVG-Datei
    # dwg.save()
    # Ausgabe als Text
    return dwg.tostring()


if __name__ == "__main__":

    # Bereich des Messtischblatts
    # (horizontal (x) 33-54,
    # vertikal (y) 24-46)
    vertical_size = (24, 46)
    horizontal_size = (33, 54)
    
    # Größe der Kästchen in Pixeln
    box_size = 50

    dbanswer = [(3328,5),
                (3830,10),
                (4138,1),
                (5446,3),
                (4634,99)]

    # Er<stellen des Messtischblatts
    create_measure_sheet(vertical_size,
                         horizontal_size,
                         box_size,
                         dataset=dbanswer)
