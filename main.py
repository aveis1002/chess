import pygame as p
from chess_engine import GameState, Move, find_best_move_alphabeta

# Constants
WIDTH = HEIGHT = 512 # 400 is another good option
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

def load_images():
    """Load all piece images once."""
    pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        # **IMPORTANT: You must have a folder named 'images' 
        # with files like 'wP.png', 'bR.png', etc.**
        IMAGES[piece] = p.transform.scale(p.image.load(f"images/{piece}.png"), (SQ_SIZE, SQ_SIZE))

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    p.display.set_caption("Human vs. Human Chess")
    clock = p.time.Clock()
    
    gs = GameState()
    # Ensure you have your piece images correctly saved as PNGs!
    load_images() 
    
    running = True
    square_selected = () # no square selected, keeps track of (row, col)
    player_clicks = [] # keeps track of two tuples: [(r1, c1), (r2, c2)]
    
    # Settings
    PLAYER_ONE = True  # White is human
    PLAYER_TWO = True  # Black is human (Changed from False for H vs. H)
    AI_DEPTH = 3       # This setting is now ignored
    
    valid_moves = gs.get_all_valid_moves() # Pre-calculate first set of valid moves
    move_made = False # Flag for when a move is made

    while running:
        human_turn = (gs.white_to_move and PLAYER_ONE) or (not gs.white_to_move and PLAYER_TWO)

        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            
            # --- Handle Mouse Input ---
            elif e.type == p.MOUSEBUTTONDOWN and human_turn:
                if not gs.game_over:
                    location = p.mouse.get_pos() # (x, y) location of mouse
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    
                    if square_selected == (row, col): # User clicked the same square twice (Deselect)
                        square_selected = () 
                        player_clicks = [] 
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected) 
                    
                    if len(player_clicks) == 2: # Two squares clicked (start and end)
                        move = Move(player_clicks[0], player_clicks[1], gs.board)
                        
                        # --- Check Move Validity ---
                        if move in valid_moves:
                            gs.make_move(move)
                            move_made = True
                            print(f"Move made: {move.get_chess_notation()}")
                        else:
                            # Invalid move, reset for next attempt
                            player_clicks = [square_selected]
                        
                        # Reset for next click cycle
                        if move_made:
                            square_selected = ()
                            player_clicks = []

            # --- Handle Keyboard Input ---
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: # 'z' key to undo
                    gs.undo_move()
                    move_made = True # Force recalculation of moves
                    gs.game_over = False
                elif e.key == p.K_r: # 'r' key to reset board (optional)
                    gs = GameState()
                    valid_moves = gs.get_all_valid_moves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False

        # --- Update Game State after a move is successfully made ---
        if move_made:
            valid_moves = gs.get_all_valid_moves()
            move_made = False
        
        # NOTE: AI block is skipped since PLAYER_TWO is True

        # --- Drawing the Game State ---
        draw_game_state(screen, gs, square_selected)
        
        # Display game status
        if gs.game_over:
            # Check the actual check status to display the correct game ending
            if gs.check_for_pins_and_checks():
                text = "Checkmate" 
            else:
                text = "Stalemate"
            
            draw_text(screen, text)

        clock.tick(MAX_FPS)
        p.display.flip()

def draw_game_state(screen, gs, sq_selected):
    """Draws the board, the pieces, and any highlights."""
    draw_board(screen) 
    highlight_squares(screen, gs, sq_selected)
    draw_pieces(screen, gs.board)

def draw_board(screen):
    """Draws the squares on the board."""
    colors = [p.Color("light gray"), p.Color("dark green")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def highlight_squares(screen, gs, sq_selected):
    """Highlights the selected square."""
    if sq_selected != ():
        r, c = sq_selected
        # Check if the piece belongs to the current player
        if (gs.board[r][c][0] == 'w' and gs.white_to_move) or \
           (gs.board[r][c][0] == 'b' and not gs.white_to_move):
            # Highlight selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100) # transparency value
            s.fill(p.Color('yellow'))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

def draw_pieces(screen, board):
    """Draws the pieces on the board using the loaded IMAGES."""
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_text(screen, text):
    """Draws game over text."""
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, 0, p.Color('Black'))
    text_location = p.Rect(0, 0, WIDTH, HEIGHT).move((WIDTH - text_object.get_width()) // 2, (HEIGHT - text_object.get_height()) // 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, p.Color("Gray"))
    screen.blit(text_object, text_location.move(2, 2))

if __name__ == "__main__":
    main()