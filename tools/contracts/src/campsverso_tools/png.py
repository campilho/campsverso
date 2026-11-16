"""PNG mínimo em Python puro (8 bits, sem entrelaçar): ler, recortar, colar e gravar em RGBA.

Serve às ferramentas que montam a arte a partir das folhas desenhadas (a arte do escritório,
ADR-0082), sem dependência nova: o resultado sai igual a cada rodada, byte a byte.
"""

import struct
import zlib
from pathlib import Path

type Px = tuple[int, int, int, int]
type Img = list[list[Px]]
CLEAR: Px = (0, 0, 0, 0)


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def read_png(path: Path) -> Img:
    """A imagem em linhas de pixels RGBA. Aceita RGBA, RGB e paleta, em 8 bits."""
    data = path.read_bytes()
    pos, idat, palette, trns = 8, b"", list[tuple[int, int, int]](), b""
    width = height = ctype = 0
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        kind, body = data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or interlace != 0:
                raise ValueError(f"{path}: só 8 bits sem entrelaçar")
        elif kind == b"PLTE":
            palette = [(body[i], body[i + 1], body[i + 2]) for i in range(0, len(body), 3)]
        elif kind == b"tRNS":
            trns = body
        elif kind == b"IDAT":
            idat += body
    channels = {2: 3, 3: 1, 6: 4}.get(ctype)
    if channels is None:
        raise ValueError(f"{path}: tipo de cor {ctype}")
    raw, stride = zlib.decompress(idat), width * channels
    prev, rows, i = bytearray(stride), list[bytearray](), 0
    for _ in range(height):
        kind_of_filter, line = raw[i], bytearray(raw[i + 1 : i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - channels] if x >= channels else 0
            b, c = prev[x], (prev[x - channels] if x >= channels else 0)
            add = (0, a, b, (a + b) // 2, _paeth(a, b, c))[kind_of_filter]
            line[x] = (line[x] + add) & 255
        rows.append(line)
        prev = line
    image: Img = []
    for line in rows:
        if ctype == 6:
            image.append(
                [(line[x], line[x + 1], line[x + 2], line[x + 3]) for x in range(0, stride, 4)]
            )
        elif ctype == 3:
            image.append([(*palette[k], trns[k] if k < len(trns) else 255) for k in line])
        else:
            image.append([(line[x], line[x + 1], line[x + 2], 255) for x in range(0, stride, 3)])
    return image


def encode_png(image: Img) -> bytes:
    """Os bytes do PNG RGBA, sem filtro e com a compressão máxima: o mesmo arquivo a cada vez."""
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in image)

    def chunk(kind: bytes, body: bytes) -> bytes:
        crc = zlib.crc32(kind + body) & 0xFFFFFFFF
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", len(image[0]), len(image), 8, 6, 0, 0, 0)
    body = chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + body


def blank(width: int, height: int, fill: Px = CLEAR) -> Img:
    return [[fill] * width for _ in range(height)]


def crop(image: Img, x: int, y: int, width: int, height: int) -> Img:
    return [row[x : x + width] for row in image[y : y + height]]


def paste(target: Img, piece: Img, x: int, y: int) -> None:
    """Cola `piece` em `target` com o canto de cima à esquerda em (x, y), sem misturar cores."""
    for dy, row in enumerate(piece):
        target[y + dy][x : x + len(row)] = row


def paste_over(target: Img, piece: Img, x: int, y: int) -> None:
    """Cola `piece` por cima de `target`, pulando os pixels transparentes (a marmita na mesinha)."""
    for dy, row in enumerate(piece):
        for dx, pixel in enumerate(row):
            if pixel[3] != 0:
                target[y + dy][x + dx] = pixel
