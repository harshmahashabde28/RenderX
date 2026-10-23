"""Application state machine managing navigation between launcher, modes, and menus."""
from enum import Enum, auto
from typing import Optional, Callable


class AppState(str, Enum):
    SPLASH = "Splash"
    MAIN_MENU = "Main Menu"
    PLAY = "Play"
    EXPLORE = "Explore"
    LEARN = "Learn"
    SETTINGS = "Settings"
    ABOUT = "About"
    TOUR = "First-Run Tour"
    PAUSE = "Paused"


class StateMachine:
    """Coordinates active application state, previous state stack, and transitions."""

    def __init__(self, initial_state: AppState = AppState.SPLASH):
        self.current_state = initial_state
        self.previous_state: Optional[AppState] = None
        self.fade_alpha: float = 255.0  # Start fully black for fade-in
        self.transitioning: bool = False
        self.target_state: Optional[AppState] = None
        self.on_state_change: Optional[Callable[[AppState], None]] = None

    def change_state(self, new_state: AppState) -> None:
        if new_state == self.current_state:
            return
        self.previous_state = self.current_state
        self.current_state = new_state
        if self.on_state_change:
            self.on_state_change(new_state)

    def start_transition(self, target_state: AppState) -> None:
        """Begin smooth fade-to-black screen transition."""
        self.target_state = target_state
        self.transitioning = True

    def update(self, dt: float) -> None:
        """Tick transition fade timers."""
        if self.transitioning:
            self.fade_alpha += 900.0 * dt
            if self.fade_alpha >= 255.0:
                self.fade_alpha = 255.0
                if self.target_state:
                    self.change_state(self.target_state)
                    self.target_state = None
                self.transitioning = False
        else:
            if self.fade_alpha > 0.0:
                self.fade_alpha = max(0.0, self.fade_alpha - 900.0 * dt)
