"""Terminal chess simulator with legal move enforcement.

This module provides a minimal ASCII chess UI for two human players.

Examples:
    >>> square_to_coords("a1")
    (7, 0)
    >>> coords_to_square((0, 7))
    'h8'
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional, Tuple

BOARD_SIZE = 8
FILES = "abcdefgh"
RANKS = "12345678"
PROMOTION_PIECES = ("q", "r", "b", "n")


@dataclass(frozen=True)
class Move:
    """A chess move in board coordinates."""

    start: Tuple[int, int]
    end: Tuple[int, int]
    promotion: Optional[str] = None
    is_castle: bool = False
    is_en_passant: bool = False


@dataclass
class GameState:
    """Mutable game state for a chess match."""

    board: List[List[str]]
    turn: str
    castling_rights: str
    en_passant: Optional[Tuple[int, int]]
    halfmove_clock: int
    fullmove_number: int


def square_to_coords(square: str) -> Tuple[int, int]:
    """Convert algebraic square (e.g., 'e2') to matrix coordinates.

    Args:
        square: Algebraic square.

    Returns:
        Row, column tuple.

    Examples:
        >>> square_to_coords("e2")
        (6, 4)
    """
    file_char, rank_char = square[0], square[1]
    col = FILES.index(file_char)
    row = BOARD_SIZE - int(rank_char)
    return row, col


def coords_to_square(coords: Tuple[int, int]) -> str:
    """Convert matrix coordinates to algebraic square.

    Examples:
        >>> coords_to_square((7, 0))
        'a1'
    """
    row, col = coords
    return f"{FILES[col]}{BOARD_SIZE - row}"


def initial_board() -> List[List[str]]:
    """Return the standard chess starting position."""
    return [
        list("rnbqkbnr"),
        list("pppppppp"),
        list("........"),
        list("........"),
        list("........"),
        list("........"),
        list("PPPPPPPP"),
        list("RNBQKBNR"),
    ]


def new_game() -> GameState:
    """Create a new game state."""
    return GameState(
        board=initial_board(),
        turn="white",
        castling_rights="KQkq",
        en_passant=None,
        halfmove_clock=0,
        fullmove_number=1,
    )


def is_white(piece: str) -> bool:
    """Return True if the piece is white."""
    return piece.isupper()


def is_black(piece: str) -> bool:
    """Return True if the piece is black."""
    return piece.islower()


def opponent(color: str) -> str:
    """Return the opposing color."""
    return "black" if color == "white" else "white"


def in_bounds(row: int, col: int) -> bool:
    """Return True if row/col are on the board."""
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def piece_belongs_to(piece: str, color: str) -> bool:
    """Return True if piece is owned by color."""
    if piece == ".":
        return False
    return is_white(piece) if color == "white" else is_black(piece)


def render_board(board: List[List[str]]) -> str:
    """Render the board as minimal ASCII."""
    lines = ["  a b c d e f g h"]
    for row in range(BOARD_SIZE):
        rank = BOARD_SIZE - row
        line = [str(rank)]
        for col in range(BOARD_SIZE):
            line.append(board[row][col])
        lines.append(" ".join(line))
    return "\n".join(lines)


def find_king(board: List[List[str]], color: str) -> Tuple[int, int]:
    """Find the king position for color."""
    target = "K" if color == "white" else "k"
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] == target:
                return row, col
    raise ValueError(f"King not found for {color}")


def iter_squares_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Yield squares between two coordinates (exclusive)."""
    start_row, start_col = start
    end_row, end_col = end
    row_step = end_row - start_row
    col_step = end_col - start_col
    if row_step != 0:
        row_step //= abs(row_step)
    if col_step != 0:
        col_step //= abs(col_step)
    row = start_row + row_step
    col = start_col + col_step
    while (row, col) != (end_row, end_col):
        yield row, col
        row += row_step
        col += col_step


def is_square_attacked(
    board: List[List[str]], square: Tuple[int, int], by_color: str
) -> bool:
    """Return True if square is attacked by by_color."""
    row, col = square
    pawn_dir = -1 if by_color == "white" else 1
    for dc in (-1, 1):
        r = row + pawn_dir
        c = col + dc
        if in_bounds(r, c):
            piece = board[r][c]
            if piece_belongs_to(piece, by_color) and piece.lower() == "p":
                return True

    knight_offsets = [
        (-2, -1),
        (-2, 1),
        (-1, -2),
        (-1, 2),
        (1, -2),
        (1, 2),
        (2, -1),
        (2, 1),
    ]
    for dr, dc in knight_offsets:
        r = row + dr
        c = col + dc
        if in_bounds(r, c):
            piece = board[r][c]
            if piece_belongs_to(piece, by_color) and piece.lower() == "n":
                return True

    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    ]
    for dr, dc in directions:
        r = row + dr
        c = col + dc
        while in_bounds(r, c):
            piece = board[r][c]
            if piece != ".":
                if not piece_belongs_to(piece, by_color):
                    break
                lower = piece.lower()
                if dr == 0 or dc == 0:
                    if lower in ("r", "q"):
                        return True
                if dr != 0 and dc != 0:
                    if lower in ("b", "q"):
                        return True
                if (r, c) == (row + dr, col + dc) and lower == "k":
                    return True
                break
            r += dr
            c += dc
    return False


def is_in_check(board: List[List[str]], color: str) -> bool:
    """Return True if color's king is in check."""
    king_pos = find_king(board, color)
    return is_square_attacked(board, king_pos, opponent(color))


def generate_pawn_moves(
    state: GameState,
    row: int,
    col: int,
    color: str,
) -> Iterator[Move]:
    """Yield pawn moves from a square."""
    board = state.board
    direction = -1 if color == "white" else 1
    start_row = 6 if color == "white" else 1
    promotion_row = 0 if color == "white" else 7

    one_row = row + direction
    if in_bounds(one_row, col) and board[one_row][col] == ".":
        if one_row == promotion_row:
            for promo in PROMOTION_PIECES:
                yield Move((row, col), (one_row, col), promotion=promo)
        else:
            yield Move((row, col), (one_row, col))
            two_row = row + 2 * direction
            if row == start_row and board[two_row][col] == ".":
                yield Move((row, col), (two_row, col))

    for dc in (-1, 1):
        capture_row = row + direction
        capture_col = col + dc
        if not in_bounds(capture_row, capture_col):
            continue
        target = board[capture_row][capture_col]
        if target != "." and not piece_belongs_to(target, color):
            if capture_row == promotion_row:
                for promo in PROMOTION_PIECES:
                    yield Move((row, col), (capture_row, capture_col), promotion=promo)
            else:
                yield Move((row, col), (capture_row, capture_col))

    if state.en_passant:
        ep_row, ep_col = state.en_passant
        if ep_row == row + direction and abs(ep_col - col) == 1:
            yield Move((row, col), (ep_row, ep_col), is_en_passant=True)


def generate_knight_moves(
    board: List[List[str]], row: int, col: int, color: str
) -> Iterator[Move]:
    """Yield knight moves from a square."""
    offsets = [
        (-2, -1),
        (-2, 1),
        (-1, -2),
        (-1, 2),
        (1, -2),
        (1, 2),
        (2, -1),
        (2, 1),
    ]
    for dr, dc in offsets:
        r = row + dr
        c = col + dc
        if in_bounds(r, c):
            target = board[r][c]
            if target == "." or not piece_belongs_to(target, color):
                yield Move((row, col), (r, c))


def generate_sliding_moves(
    board: List[List[str]],
    row: int,
    col: int,
    color: str,
    directions: Iterable[Tuple[int, int]],
) -> Iterator[Move]:
    """Yield sliding moves (rook, bishop, queen)."""
    for dr, dc in directions:
        r = row + dr
        c = col + dc
        while in_bounds(r, c):
            target = board[r][c]
            if target == ".":
                yield Move((row, col), (r, c))
            else:
                if not piece_belongs_to(target, color):
                    yield Move((row, col), (r, c))
                break
            r += dr
            c += dc


def generate_king_moves(
    state: GameState, row: int, col: int, color: str
) -> Iterator[Move]:
    """Yield king moves, including castling."""
    board = state.board
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            r = row + dr
            c = col + dc
            if in_bounds(r, c):
                target = board[r][c]
                if target == "." or not piece_belongs_to(target, color):
                    yield Move((row, col), (r, c))

    if color == "white" and (row, col) == (7, 4):
        if "K" in state.castling_rights:
            if board[7][7] == "R" and board[7][5] == "." and board[7][6] == ".":
                if (
                    not is_in_check(board, color)
                    and not is_square_attacked(board, (7, 5), "black")
                    and not is_square_attacked(board, (7, 6), "black")
                ):
                    yield Move((7, 4), (7, 6), is_castle=True)
        if "Q" in state.castling_rights:
            if (
                board[7][0] == "R"
                and board[7][1] == "."
                and board[7][2] == "."
                and board[7][3] == "."
            ):
                if (
                    not is_in_check(board, color)
                    and not is_square_attacked(board, (7, 3), "black")
                    and not is_square_attacked(board, (7, 2), "black")
                ):
                    yield Move((7, 4), (7, 2), is_castle=True)

    if color == "black" and (row, col) == (0, 4):
        if "k" in state.castling_rights:
            if board[0][7] == "r" and board[0][5] == "." and board[0][6] == ".":
                if (
                    not is_in_check(board, color)
                    and not is_square_attacked(board, (0, 5), "white")
                    and not is_square_attacked(board, (0, 6), "white")
                ):
                    yield Move((0, 4), (0, 6), is_castle=True)
        if "q" in state.castling_rights:
            if (
                board[0][0] == "r"
                and board[0][1] == "."
                and board[0][2] == "."
                and board[0][3] == "."
            ):
                if (
                    not is_in_check(board, color)
                    and not is_square_attacked(board, (0, 3), "white")
                    and not is_square_attacked(board, (0, 2), "white")
                ):
                    yield Move((0, 4), (0, 2), is_castle=True)


def generate_pseudo_legal_moves(state: GameState, color: str) -> Iterator[Move]:
    """Yield pseudo-legal moves (ignores self-check)."""
    board = state.board
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board[row][col]
            if not piece_belongs_to(piece, color):
                continue
            lower = piece.lower()
            if lower == "p":
                yield from generate_pawn_moves(state, row, col, color)
            elif lower == "n":
                yield from generate_knight_moves(board, row, col, color)
            elif lower == "b":
                yield from generate_sliding_moves(
                    board,
                    row,
                    col,
                    color,
                    [(-1, -1), (-1, 1), (1, -1), (1, 1)],
                )
            elif lower == "r":
                yield from generate_sliding_moves(
                    board,
                    row,
                    col,
                    color,
                    [(-1, 0), (1, 0), (0, -1), (0, 1)],
                )
            elif lower == "q":
                yield from generate_sliding_moves(
                    board,
                    row,
                    col,
                    color,
                    [
                        (-1, 0),
                        (1, 0),
                        (0, -1),
                        (0, 1),
                        (-1, -1),
                        (-1, 1),
                        (1, -1),
                        (1, 1),
                    ],
                )
            elif lower == "k":
                yield from generate_king_moves(state, row, col, color)


def apply_move(state: GameState, move: Move) -> GameState:
    """Apply a move and return the new state."""
    board = [row.copy() for row in state.board]
    start_row, start_col = move.start
    end_row, end_col = move.end
    piece = board[start_row][start_col]
    target = board[end_row][end_col]
    board[start_row][start_col] = "."

    promotion = move.promotion
    if piece.lower() == "p" and (end_row == 0 or end_row == 7):
        promotion = promotion or "q"
        piece = promotion.upper() if piece.isupper() else promotion.lower()

    if move.is_en_passant:
        capture_row = start_row
        capture_col = end_col
        board[capture_row][capture_col] = "."

    if move.is_castle:
        if end_col == 6:
            rook_start = (end_row, 7)
            rook_end = (end_row, 5)
        else:
            rook_start = (end_row, 0)
            rook_end = (end_row, 3)
        rook_piece = board[rook_start[0]][rook_start[1]]
        board[rook_start[0]][rook_start[1]] = "."
        board[rook_end[0]][rook_end[1]] = rook_piece

    board[end_row][end_col] = piece

    castling_rights = state.castling_rights
    if piece.lower() == "k":
        if piece.isupper():
            castling_rights = castling_rights.replace("K", "").replace("Q", "")
        else:
            castling_rights = castling_rights.replace("k", "").replace("q", "")
    if piece.lower() == "r":
        if move.start == (7, 0):
            castling_rights = castling_rights.replace("Q", "")
        if move.start == (7, 7):
            castling_rights = castling_rights.replace("K", "")
        if move.start == (0, 0):
            castling_rights = castling_rights.replace("q", "")
        if move.start == (0, 7):
            castling_rights = castling_rights.replace("k", "")
    if target.lower() == "r":
        if move.end == (7, 0):
            castling_rights = castling_rights.replace("Q", "")
        if move.end == (7, 7):
            castling_rights = castling_rights.replace("K", "")
        if move.end == (0, 0):
            castling_rights = castling_rights.replace("q", "")
        if move.end == (0, 7):
            castling_rights = castling_rights.replace("k", "")

    en_passant = None
    if piece.lower() == "p" and abs(end_row - start_row) == 2:
        en_passant = ((start_row + end_row) // 2, start_col)

    halfmove_clock = (
        0 if piece.lower() == "p" or target != "." else state.halfmove_clock + 1
    )
    fullmove_number = state.fullmove_number + (1 if state.turn == "black" else 0)

    return GameState(
        board=board,
        turn=opponent(state.turn),
        castling_rights=castling_rights,
        en_passant=en_passant,
        halfmove_clock=halfmove_clock,
        fullmove_number=fullmove_number,
    )


def generate_legal_moves(state: GameState, color: str) -> List[Move]:
    """Return a list of legal moves for color."""
    legal_moves: List[Move] = []
    for move in generate_pseudo_legal_moves(state, color):
        next_state = apply_move(state, move)
        if not is_in_check(next_state.board, color):
            legal_moves.append(move)
    return legal_moves


def parse_move_text(text: str) -> Optional[Move]:
    """Parse move text like 'e2e4' or 'e7e8q'."""
    cleaned = text.replace(" ", "").lower()
    if len(cleaned) not in (4, 5):
        return None
    if cleaned[0] not in FILES or cleaned[2] not in FILES:
        return None
    if cleaned[1] not in RANKS or cleaned[3] not in RANKS:
        return None
    promotion = None
    if len(cleaned) == 5:
        if cleaned[4] not in PROMOTION_PIECES:
            return None
        promotion = cleaned[4]
    start = square_to_coords(cleaned[:2])
    end = square_to_coords(cleaned[2:4])
    return Move(start, end, promotion=promotion)


def format_move(move: Move) -> str:
    """Format a move for display."""
    text = f"{coords_to_square(move.start)}{coords_to_square(move.end)}"
    if move.promotion:
        text += move.promotion
    return text


def status_line(state: GameState) -> str:
    """Return a status line with turn info."""
    return f"Turn: {state.turn}  Move: {state.fullmove_number}"


def choose_move(
    state: GameState, legal_moves: List[Move], move_text: str
) -> Optional[Move]:
    """Match user input against legal moves."""
    parsed = parse_move_text(move_text)
    if not parsed:
        return None
    for move in legal_moves:
        if move.start == parsed.start and move.end == parsed.end:
            if move.promotion == parsed.promotion or parsed.promotion is None:
                return Move(
                    move.start,
                    move.end,
                    promotion=parsed.promotion or move.promotion,
                    is_castle=move.is_castle,
                    is_en_passant=move.is_en_passant,
                )
    return None


def describe_outcome(state: GameState, legal_moves: List[Move]) -> Optional[str]:
    """Return game-ending status, if any."""
    if legal_moves:
        return None
    if is_in_check(state.board, state.turn):
        winner = opponent(state.turn)
        return f"Checkmate. {winner} wins."
    return "Stalemate."


def print_help() -> None:
    """Print command help."""
    print("Enter moves like e2e4 or e7e8q for promotion.")
    print("Commands: help, quit")


def main() -> None:
    """Run the terminal chess simulator."""
    state = new_game()
    print("Matrix Chess Simulator (terminal)")
    print_help()
    while True:
        print()
        print(render_board(state.board))
        print(status_line(state))
        legal_moves = generate_legal_moves(state, state.turn)
        outcome = describe_outcome(state, legal_moves)
        if outcome:
            print(outcome)
            break
        if is_in_check(state.board, state.turn):
            print("Check.")
        move_text = input("Move> ").strip()
        if not move_text:
            continue
        if move_text.lower() in {"quit", "exit"}:
            print("Game ended.")
            break
        if move_text.lower() == "help":
            print_help()
            continue
        chosen = choose_move(state, legal_moves, move_text)
        if not chosen:
            print("Illegal move. Use 'help' for format.")
            continue
        state = apply_move(state, chosen)


if __name__ == "__main__":
    main()
