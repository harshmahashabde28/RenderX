from enum import Enum

class GameState(Enum):
    MAIN_MENU = 1
    PLAY_SETUP = 2
    SETTINGS = 3
    GAMEPLAY = 4
    PAUSED = 5
    GAME_OVER = "GAME_OVER"

class StateMachine:
    def __init__(self):
        # The game always starts on the Main Menu
        self.current_state = GameState.MAIN_MENU

    def change_state(self, new_state):
        print(f"State changed: {self.current_state.name} -> {new_state.name}")
        self.current_state = new_state