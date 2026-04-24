class GameState:
    """Represents the current state of the chessboard and handles move generation."""
    def __init__(self):
        # 8x8 list of lists. 'wB' is White Bishop, 'bR' is Black Rook, '--' is empty.
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        
        self.white_to_move = True
        self.move_log = []
        self.game_over = False
        
        # Track King positions for quick check-checking
        self.wK_loc = (7, 4)
        self.bK_loc = (0, 4)
        
        # En Passant and Castling Rights omitted for initial implementation brevity

    def make_move(self, move):
        """Updates the board state based on a valid move."""
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move # Switch turn
        
        # Update King's location
        if move.piece_moved == 'wK':
            self.wK_loc = (move.end_row, move.end_col)
        elif move.piece_moved == 'bK':
            self.bK_loc = (move.end_row, move.end_col)

    def undo_move(self):
        """Undoes the last move, useful for the search algorithm."""
        if self.move_log:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move
            
            # Update King's location
            if move.piece_moved == 'wK':
                self.wK_loc = (move.start_row, move.start_col)
            elif move.piece_moved == 'bK':
                self.bK_loc = (move.start_row, move.start_col)

# --- Check Detection and Validation ---

    def get_all_valid_moves(self):
        """
        Finds all moves, filters them to ensure the King is not in check, 
        and updates game_over status for Checkmate/Stalemate.
        """
        
        # 1. Generate all possible moves (without checking for self-check)
        moves = self.get_all_possible_moves()
        
        # 2. Filter moves that put King in check (This is the slow, but accurate part)
        # Go backwards through the move list, making and unmaking each move
        for i in range(len(moves) - 1, -1, -1): 
            move = moves[i]
            self.make_move(move)
            
            # Temporarily switch turn to check if the King is attacked by the opponent
            self.white_to_move = not self.white_to_move 
            if self.is_in_check():
                moves.remove(move) # Move is illegal
            self.white_to_move = not self.white_to_move # Switch turn back
            
            self.undo_move() # Undo the move

        # 3. Correct Checkmate/Stalemate Determination
        if len(moves) == 0:
            if self.check_for_pins_and_checks():
                self.game_over = True # Checkmate (No legal moves AND King is in check)
            else:
                self.game_over = True # Stalemate (No legal moves AND King is NOT in check)
        else:
            self.game_over = False # Game continues

        return moves

    def is_in_check(self):
        """Checks if the King of the current player is attacked by the opponent."""
        if self.white_to_move:
            king_r, king_c = self.wK_loc
        else:
            king_r, king_c = self.bK_loc
            
        return self.is_square_attacked(king_r, king_c)

    def is_square_attacked(self, r, c):
        """Checks if the square (r, c) is attacked by the OPPONENT."""
        # Switch turn temporarily to check opposition's moves
        self.white_to_move = not self.white_to_move 
        opp_moves = self.get_all_possible_moves()
        self.white_to_move = not self.white_to_move # Switch turn back
        
        for move in opp_moves:
            if move.end_row == r and move.end_col == c:
                return True
        return False

    def check_for_pins_and_checks(self):
        """
        [NEW] Checks if the current King is in check using a direct scan. 
        This is necessary for the Checkmate/Stalemate logic.
        """
        if self.white_to_move:
            king_r, king_c = self.wK_loc
            ally_color = 'w'
            enemy_color = 'b'
        else:
            king_r, king_c = self.bK_loc
            ally_color = 'b'
            enemy_color = 'w'

        # Directions for sliding pieces: Rook/Queen (0-3) and Bishop/Queen (4-7)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)] 
        
        # 1. Sliding Pieces Check
        for j, (dr, dc) in enumerate(directions):
            for i in range(1, 8):
                end_r, end_c = king_r + dr * i, king_c + dc * i
                
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    end_piece = self.board[end_r][end_c]
                    if end_piece[0] == ally_color: # Friendly piece encountered
                        break
                    
                    if end_piece[0] == enemy_color: # Enemy piece encountered
                        piece_type = end_piece[1]
                        
                        is_rook_like_threat = (0 <= j <= 3 and piece_type == 'R')
                        is_bishop_like_threat = (4 <= j <= 7 and piece_type == 'B')
                        is_queen_threat = (piece_type == 'Q')
                        
                        if is_rook_like_threat or is_bishop_like_threat or is_queen_threat:
                            return True
                        else: 
                            break # Enemy piece, but not a threat on this line
                else:
                    break

        # 2. Knight Checks
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in knight_moves:
            end_r, end_c = king_r + dr, king_c + dc
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                if end_piece[0] == enemy_color and end_piece[1] == 'N':
                    return True

        # 3. Pawn Checks
        pawn_direction = -1 if ally_color == 'w' else 1
        pawn_captures = [(king_r + pawn_direction, king_c - 1), (king_r + pawn_direction, king_c + 1)]

        for end_r, end_c in pawn_captures:
             if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                if end_piece[0] == enemy_color and end_piece[1] == 'P':
                    return True
        
        # 4. King Checks (Opponent's King next to ours)
        # This prevents the King from moving into a square next to the enemy King
        for dr, dc in directions:
             end_r, end_c = king_r + dr, king_c + dc
             if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                if end_piece[0] == enemy_color and end_piece[1] == 'K':
                    return True

        return False # No checks found

    def get_all_possible_moves(self):
        """Generates all moves without checking for legality (used by is_in_check)."""
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == "--":
                    continue
                
                turn = piece[0]
                piece_type = piece[1]
                
                if (turn == 'w' and self.white_to_move) or (turn == 'b' and not self.white_to_move):
                    
                    if piece_type == 'P':
                        self._get_pawn_moves(r, c, moves)
                    elif piece_type == 'R':
                        self._get_rook_moves(r, c, moves)
                    elif piece_type == 'N':
                        self._get_knight_moves(r, c, moves)
                    elif piece_type == 'B':
                        self._get_bishop_moves(r, c, moves)
                    elif piece_type == 'Q':
                        self._get_queen_moves(r, c, moves)
                    elif piece_type == 'K':
                        self._get_king_moves(r, c, moves)
        return moves

# --- Piece Specific Movement Implementations ---

    def _get_pawn_moves(self, r, c, moves):
        """Generates all legal pawn moves for the pawn at (r, c)."""
        piece_color = self.board[r][c][0]
        direction = -1 if piece_color == 'w' else 1
        start_row = 6 if piece_color == 'w' else 1
        
        # 1. Single Square Forward
        end_r = r + direction
        if 0 <= end_r < 8 and self.board[end_r][c] == "--":
            moves.append(Move((r, c), (end_r, c), self.board))
            
            # 2. Initial Two-Square Move
            if r == start_row and self.board[r + 2 * direction][c] == "--":
                moves.append(Move((r, c), (r + 2 * direction, c), self.board))
        
        # 3. Captures (Diagonal)
        for dc in [-1, 1]:
            end_c = c + dc
            end_r = r + direction
            if 0 <= end_c < 8 and 0 <= end_r < 8:
                end_piece = self.board[end_r][end_c]
                if end_piece != "--" and end_piece[0] != piece_color:
                    moves.append(Move((r, c), (end_r, end_c), self.board))

    def _get_rook_moves(self, r, c, moves):
        """Generates moves along ranks and files."""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] 
        self._get_sliding_moves(r, c, moves, directions)

    def _get_bishop_moves(self, r, c, moves):
        """Generates moves along diagonals."""
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] 
        self._get_sliding_moves(r, c, moves, directions)

    def _get_queen_moves(self, r, c, moves):
        """Generates moves along ranks, files, and diagonals."""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        self._get_sliding_moves(r, c, moves, directions)

    def _get_sliding_moves(self, r, c, moves, directions):
        """Helper for Rook, Bishop, Queen (sliding pieces)."""
        piece_color = self.board[r][c][0]
        
        for dr, dc in directions:
            for i in range(1, 8): # Max distance of 7 squares
                end_r, end_c = r + dr * i, c + dc * i
                
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    end_piece = self.board[end_r][end_c]
                    
                    if end_piece == "--": # Empty square
                        moves.append(Move((r, c), (end_r, end_c), self.board))
                    elif end_piece[0] != piece_color: # Capture (Opponent piece)
                        moves.append(Move((r, c), (end_r, end_c), self.board))
                        break # Stop after capture
                    else: # Friendly piece (Blocked)
                        break
                else: # Off board
                    break

    def _get_knight_moves(self, r, c, moves):
        """Generates moves for the Knight (L-shape)."""
        piece_color = self.board[r][c][0]
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        
        for dr, dc in knight_moves:
            end_r, end_c = r + dr, c + dc
            
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                
                if end_piece == "--" or end_piece[0] != piece_color:
                    moves.append(Move((r, c), (end_r, end_c), self.board))

    def _get_king_moves(self, r, c, moves):
        """Generates moves for the King (1 square in any direction)."""
        piece_color = self.board[r][c][0]
        king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        for dr, dc in king_moves:
            end_r, end_c = r + dr, c + dc
            
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                
                if end_piece == "--" or end_piece[0] != piece_color:
                    moves.append(Move((r, c), (end_r, end_c), self.board))

# --- Move Class (No Change Needed) ---

class Move:
    """Stores information about a move."""
    RanksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    RowsToRanks = {v: k for k, v in RanksToRows.items()}
    FilesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    ColsToFiles = {v: k for k, v in FilesToCols.items()}

    def __init__(self, start_sq, end_sq, board):
        self.start_row, self.start_col = start_sq
        self.end_row, self.end_col = end_sq
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        self.move_id = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False
    
    def get_chess_notation(self):
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, r, c):
        return self.ColsToFiles[c] + self.RowsToRanks[r]

# --- AI (Alpha-Beta Pruning - No Change Needed) ---

# Simple material evaluation dictionary
PIECE_SCORES = {"K": 0, "Q": 90, "R": 50, "B": 30, "N": 30, "P": 10, "--": 0}

def evaluate_board(gs):
    """Scores the board state based on material advantage."""
    if gs.game_over:
        return 0
        
    score = 0
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece != "--":
                color = piece[0]
                piece_type = piece[1]
                
                # Simple Material Evaluation
                value = PIECE_SCORES[piece_type]
                
                if color == 'w':
                    score += value
                else:
                    score -= value
                    
    return score

def find_best_move_alphabeta(gs, depth):
    """Entry point for the AI search."""
    return alpha_beta_search(gs, depth, -float('inf'), float('inf'), gs.white_to_move)[1]

def alpha_beta_search(gs, depth, alpha, beta, is_maximizing_player):
    """Minimax search with Alpha-Beta Pruning."""
    if depth == 0 or gs.game_over:
        return evaluate_board(gs), None

    # Get valid moves (filtered for check/mate)
    valid_moves = gs.get_all_valid_moves() 
    best_move = None
    
    if is_maximizing_player: # White/AI
        max_eval = -float('inf')
        for move in valid_moves:
            gs.make_move(move)
            eval, _ = alpha_beta_search(gs, depth - 1, alpha, beta, False)
            gs.undo_move()
            
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break # Beta cut-off
        return max_eval, best_move
    
    else: # Minimizing Player (Black)
        min_eval = float('inf')
        for move in valid_moves:
            gs.make_move(move)
            eval, _ = alpha_beta_search(gs, depth - 1, alpha, beta, True)
            gs.undo_move()
            
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break # Alpha cut-off
        return min_eval, best_move