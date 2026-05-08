"""
Utility script to generate a beginner-friendly PDF that explains the
construction of the neon-styled Tetris game implemented in ``tetris.py``.
The script avoids external dependencies by emitting a minimal PDF with
plain text, making it easy to regenerate in constrained environments.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

PAGE_WIDTH = 612  # 8.5in * 72pt
PAGE_HEIGHT = 792  # 11in * 72pt
MARGIN = 54
LINE_HEIGHT = 16
FONT_SIZE = 12
FONT_OBJECT_NUMBER = 3  # Fixed to simplify references


def escape_pdf_text(text: str) -> str:
    """Escape characters that have special meaning inside PDF text strings."""
    return text.replace("\\", r"\\\\").replace("(", r"\\(").replace(")", r"\\)")


def wrap_paragraph(text: str, width: int = 88) -> list[str]:
    return textwrap.wrap(text, width=width) if text else [""]


def build_pages(lines: list[str]) -> list[str]:
    pages_streams = []
    y = PAGE_HEIGHT - MARGIN
    current_stream_lines = []

    def flush_page():
        nonlocal current_stream_lines
        pages_streams.append("\n".join(current_stream_lines) + "\n")
        current_stream_lines = []

    for line in lines:
        if y < MARGIN:
            flush_page()
            y = PAGE_HEIGHT - MARGIN
        if not line:
            y -= LINE_HEIGHT
            continue
        escaped = escape_pdf_text(line)
        current_stream_lines.append(
            f"BT /F1 {FONT_SIZE} Tf {MARGIN} {y} Td ({escaped}) Tj ET"
        )
        y -= LINE_HEIGHT
    flush_page()
    return pages_streams


def assemble_pdf(lines: list[str]) -> bytes:
    pages_streams = build_pages(lines)

    objects: list[str] = []

    def add_object(body: str) -> int:
        objects.append(body)
        return len(objects)

    # Reserve catalog and pages objects; we'll fill pages once page numbers are known.
    catalog_placeholder = "<< /Type /Catalog /Pages 2 0 R >>"
    add_object(catalog_placeholder)  # 1 0 obj

    pages_placeholder_index = add_object("")  # 2 0 obj placeholder

    font_object = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    add_object(font_object)  # 3 0 obj

    page_numbers: list[int] = []
    for stream in pages_streams:
        length = len(stream.encode("utf-8"))
        content_obj_num = add_object(
            f"<< /Length {length} >>\nstream\n{stream}endstream"
        )
        page_obj_num = add_object(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Contents {content_obj_num} 0 R /Resources << /Font << /F1 {FONT_OBJECT_NUMBER} 0 R >> >> >>"
        )
        page_numbers.append(page_obj_num)

    kids = " ".join(f"{num} 0 R" for num in page_numbers)
    pages_obj = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_numbers)} >>"
    )
    objects[pages_placeholder_index - 1] = pages_obj

    # Build xref table
    pdf_parts = ["%PDF-1.4\n"]
    offsets = []
    for obj_number, body in enumerate(objects, start=1):
        offsets.append(sum(len(part.encode("utf-8")) for part in pdf_parts))
        pdf_parts.append(f"{obj_number} 0 obj\n{body}\nendobj\n")

    xref_offset = sum(len(part.encode("utf-8")) for part in pdf_parts)
    pdf_parts.append("xref\n")
    pdf_parts.append(f"0 {len(objects) + 1}\n")
    pdf_parts.append("0000000000 65535 f \n")
    for offset in offsets:
        pdf_parts.append(f"{offset:010d} 00000 n \n")

    pdf_parts.append(
        "trailer\n"
        f"<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    )

    return "".join(pdf_parts).encode("utf-8")


def main() -> None:
    sections = [
        ("Título", ["Guia rápido: como o Tetris em python funciona"]),
        (
            "Objetivo",
            [
                "Explicar de forma simples como o arquivo tetris.py organiza um jogo completo, para quem está começando em Python.",
                "O foco é entender a estrutura geral, sem precisar conhecer cada detalhe matemático.",
            ],
        ),
        (
            "Bibliotecas usadas",
            [
                "O jogo usa a biblioteca pygame para janela, desenhos, fontes e capturar teclado.",
                "Só precisamos do Python e do pygame instalados para rodar o tetris.py.",
            ],
        ),
        (
            "Como o código está organizado",
            [
                "Constantes definem cores, tamanhos dos blocos, velocidade e formatos das peças.",
                "A matriz grid guarda quais células do campo já estão ocupadas e suas cores.",
                "Cada peça (Tetromino) guarda posição, formato e cor. A forma é uma lista de coordenadas relativas.",
                "Há funções para rotacionar a peça, checar colisão e encaixar a peça no grid quando ela para.",
                "Um gerador sorteia a próxima peça e mantém a pré-visualização para o jogador.",
            ],
        ),
        (
            "Loop principal do jogo",
            [
                "O loop roda enquanto a janela estiver aberta ou até dar game over.",
                "A cada ciclo: lê o teclado, atualiza a peça atual, verifica colisões e redesenha a tela.",
                "Se a peça encosta no chão ou em outra peça, ela é fixada no grid e uma nova peça é criada.",
                "Linhas completas são removidas; o placar e o nível aumentam conforme o número de linhas.",
            ],
        ),
        (
            "Controles importantes",
            [
                "Setas: mover para os lados e acelerar para baixo.",
                "Barra de espaço: queda imediata (hard drop) para posicionar a peça rápido.",
                "Z ou seta para cima: rotacionar a peça.",
                "R: reinicia a partida quando quiser recomeçar.",
            ],
        ),
        (
            "Recursos visuais e efeitos",
            [
                "Plano de fundo em gradiente e grades iluminadas deixam o visual moderno.",
                "Blocos possuem brilho e sombreamento simples para parecerem peças de vidro.",
                "Uma “peça fantasma” mostra onde a peça atual vai pousar, ajudando a planejar.",
                "Partículas aparecem quando linhas são removidas, dando feedback ao jogador.",
            ],
        ),
        (
            "Por que funciona",
            [
                "A grade funciona como um tabuleiro 2D; cada peça só se move se as próximas células estiverem livres.",
                "Ao rotacionar, o código verifica se a nova posição cabe. Se não couber, volta à posição anterior.",
                "A remoção de linhas ocorre ao encontrar uma linha totalmente ocupada; depois, o restante desce.",
                "O tempo controla quando a peça cai sozinha, e aumenta a velocidade conforme o nível sobe.",
            ],
        ),
        (
            "Como estudar o arquivo",
            [
                "Leia as constantes no topo para entender as cores e tamanhos.",
                "Veja a classe ou estrutura que representa as peças e como elas rodam com uma lista de offsets.",
                "Acompanhe o loop principal no final do arquivo: nele estão as chamadas de entrada, atualização e desenho.",
                "Experimente mudar cores ou velocidades para sentir como pequenas mudanças afetam o jogo.",
            ],
        ),
        (
            "Próximos passos",
            [
                "Adicione sons para quedas e limpeza de linhas usando pygame.mixer.",
                "Crie um placar mais elaborado com recordes salvos em arquivo.",
                "Implemente modo fácil mudando a velocidade base ou aumentando o campo de jogo.",
            ],
        ),
    ]

    lines: list[str] = []
    for title, body in sections:
        lines.append(title)
        lines.append("")
        for paragraph in body:
            lines.extend(wrap_paragraph(paragraph))
            lines.append("")
        lines.append("")

    pdf_bytes = assemble_pdf(lines)
    output_path = Path("tetris_guide.pdf")
    output_path.write_bytes(pdf_bytes)
    print(f"PDF gerado em {output_path.resolve()}")


if __name__ == "__main__":
    main()
