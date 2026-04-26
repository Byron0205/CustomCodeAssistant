"""
Formateador personalizado de Markdown con tablas mejoradas.
Detecta y reformatea tablas markdown para mejor visualización.
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich import box


def parse_markdown_table(lines):
    """
    Parsea una tabla markdown y retorna (header, rows, start_idx, end_idx)
    o None si no encuentra tabla válida.
    """
    if len(lines) < 3:
        return None

    for i, line in enumerate(lines):
        if not line.strip().startswith('|'):
            continue

        # Encontró posible tabla
        header_line = lines[i]
        if i + 1 >= len(lines):
            continue

        separator_line = lines[i + 1]

        # Validar que sea tabla (separador con dashes)
        if not all(c in '|-' for c in separator_line.replace(' ', '')):
            continue

        # Parsear header
        header = [cell.strip() for cell in header_line.split('|')[1:-1]]

        # Parsear filas
        rows = []
        j = i + 2
        while j < len(lines) and lines[j].strip().startswith('|'):
            row = [cell.strip() for cell in lines[j].split('|')[1:-1]]
            if len(row) == len(header):
                rows.append(row)
            j += 1

        if rows:
            return (header, rows, i, j)

    return None


def create_rich_table(header, rows):
    """Crea una tabla Rich con bordes claros."""
    table = Table(show_header=True, header_style="bold cyan", show_lines=True, box=box.SQUARE)

    # Agregar columnas
    for col in header:
        table.add_column(col)

    # Agregar filas
    for row in rows:
        table.add_row(*row)

    return table


def format_markdown_response(text):
    """
    Formatea una respuesta markdown detectando y mejorando tablas.
    Retorna renderizado de forma óptima.
    """
    console = Console()
    lines = text.split('\n')

    # Procesar el texto buscando tablas
    output_parts = []
    i = 0

    while i < len(lines):
        # Intenta parsear tabla a partir de línea i
        result = parse_markdown_table(lines[i:])

        if result:
            header, rows, local_start, local_end = result
            actual_end = i + local_end

            # Agregar markdown antes de la tabla
            if i > 0 and any(lines[:i]):
                before_text = '\n'.join(lines[:i])
                if before_text.strip():
                    output_parts.append(('markdown', before_text))
                lines = lines[i:]
                i = 0

            # Crear tabla formateada
            table = create_rich_table(header, rows)
            output_parts.append(('table', table))

            # Continuar después de tabla
            i = local_end
            lines = lines[local_end:]
        else:
            i += 1

    # Agregar lo que quede como markdown
    remaining = '\n'.join(lines)
    if remaining.strip():
        output_parts.append(('markdown', remaining))

    return output_parts


def render_formatted_response(console, text):
    """
    Renderiza una respuesta formateada en la consola.
    Mezcla markdown normal con tablas mejoradas.
    """
    parts = format_markdown_response(text)

    for part_type, content in parts:
        if part_type == 'markdown':
            md = Markdown(content)
            console.print(md)
        elif part_type == 'table':
            console.print(content)
