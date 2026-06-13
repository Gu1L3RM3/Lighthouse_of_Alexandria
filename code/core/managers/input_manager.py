import pygame
from pygame import Vector2
import ctypes

from core.managers.language_service import LanguageService
from core.settings import (
    KEY_DIALOG,
    KEY_NEXT_SCENE,
    KEY_PLACE_BOMB,
    PLAYER_DOWN,
    PLAYER_LEFT,
    PLAYER_RIGHT,
    PLAYER_UP,
)


class InputManager:
    _instance = None

    def __init__(self):
        self.deadzone = 0.35
        self.joysticks: dict[int, pygame.joystick.Joystick] = {}
        self.controllers: dict[int, object] = {}
        self.axis_vector = Vector2(0, 0)
        self.dpad_vector = Vector2(0, 0)
        self.last_input_source = "keyboard"
        self.mouse_visible = True
        self.controller_layout = "xbox"
        self.just_pressed_keys: set[int] = set()
        self.just_pressed_actions: set[str] = set()
        self._pressed_virtual_keys: set[int] = set()
        self._pressed_actions: set[str] = set()
        self._prev_button_states: dict[int, bool] = {}
        self._prev_hat_value: tuple[int, int] = (0, 0)
        self._prev_axis_digital = {
            "left": False,
            "right": False,
            "up": False,
            "down": False,
        }
        self._xinput = None
        self._xinput_state = None
        self._xinput_connected = False
        self._virtual_mouse_target: tuple[int, int] | None = None

        self._button_to_actions_joystick = {
            0: ("confirm", "interact"),
            1: ("back",),
            2: ("bomb",),
            3: ("open_editor",),
            4: ("tool_prev",),
            5: ("tool_next",),
            8: ("menu_confirm",),  # L3 (common on generic joystick mapping)
            6: ("help",),
            7: ("pause",),
        }
        self._button_to_actions_sdl2 = {
            0: ("confirm", "interact"),
            1: ("back",),
            2: ("bomb",),
            3: ("open_editor",),
            4: ("help",),       # Back/View
            6: ("pause",),      # Start/Menu
            7: ("menu_confirm",),  # Left stick click (L3)
            9: ("tool_prev",),  # LB/L1
            10: ("tool_next",), # RB/R1
        }
        self._button_to_actions_xinput = {
            0: ("confirm", "interact"),
            1: ("back",),
            2: ("bomb",),
            3: ("open_editor",),
            4: ("tool_prev",),  # LB
            5: ("tool_next",),  # RB
            6: ("help",),       # Back
            7: ("pause",),      # Start
            8: ("menu_confirm",),  # Left thumb (L3)
        }
        self._action_to_keys = {
            "confirm": (pygame.K_RETURN, KEY_NEXT_SCENE),
            "interact": (KEY_DIALOG,),
            "back": (pygame.K_ESCAPE,),
            "bomb": (KEY_PLACE_BOMB,),
        }
        self._keyboard_action_labels = {
            "confirm": "ENTER",
            "interact": "E",
            "back": "ESC",
            "bomb": "B",
            "pause": "ESC",
            "open_editor": "CORE",
            "help": "F1",
            "tool_prev": "Q",
            "tool_next": "E",
            "menu_confirm": "L3",
            "select_tool": "S",
        }
        self._controller_action_labels_by_layout = {
            "xbox": {
                "confirm": "A",
                "interact": "A",
                "back": "B",
                "bomb": "X",
                "pause": "START",
                "open_editor": "Y",
                "help": "BACK",
                "tool_prev": "LB",
                "tool_next": "RB",
                "menu_confirm": "L3",
                "select_tool": "A",
            },
            "playstation": {
                "confirm": "CROSS",
                "interact": "CROSS",
                "back": "CIRCLE",
                "bomb": "SQUARE",
                "pause": "OPTIONS",
                "open_editor": "TRIANGLE",
                "help": "SHARE",
                "tool_prev": "L1",
                "tool_next": "R1",
                "menu_confirm": "L3",
                "select_tool": "CROSS",
            },
        }

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = InputManager()
        return cls._instance

    def initialize(self):
        self.joysticks.clear()
        self.controllers.clear()
        self._xinput_connected = False
        self._xinput_state = None
        self.axis_vector.xy = 0, 0
        self.dpad_vector.xy = 0, 0
        self.apply_mouse_visibility()

    def begin_frame(self):
        self.just_pressed_keys.clear()
        self.just_pressed_actions.clear()

    def process_events(self, events: list[pygame.event.Event]) -> list[pygame.event.Event]:
        self.begin_frame()
        augmented_events: list[pygame.event.Event] = []

        for event in events:
            augmented_events.append(event)

            if event.type == pygame.KEYDOWN:
                synthetic_controller_key = bool(getattr(event, "synthetic_controller", False))
                if synthetic_controller_key:
                    self.last_input_source = "controller"
                    self.mouse_visible = False
                    continue
                self.last_input_source = "keyboard"
                self.just_pressed_keys.add(event.key)
                self.mouse_visible = True
                continue

            if event.type == pygame.MOUSEMOTION:
                if self._virtual_mouse_target is not None and tuple(event.pos) == self._virtual_mouse_target:
                    self._virtual_mouse_target = None
                    continue
                # Quando estamos em fluxo de controle, ignora movimento de mouse
                # para evitar "flicker" de fonte por eventos sinteticos/ruido.
                if self.last_input_source == "controller" and not self.mouse_visible:
                    continue
                else:
                    self.last_input_source = "mouse"
                    self.mouse_visible = True
                continue

            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
                self.last_input_source = "mouse"
                self.mouse_visible = True
                continue

            if event.type == pygame.JOYDEVICEADDED:
                self._connect_joystick(event.device_index)
                continue

            if event.type == pygame.JOYDEVICEREMOVED:
                self._disconnect_joystick(event.instance_id)
                continue

            if event.type == pygame.JOYBUTTONDOWN:
                self.last_input_source = "controller"
                self.mouse_visible = False
                # Evita mapeamento duplicado/conflitante quando SDL2/XInput ja estao ativos.
                if self.controllers or self._xinput_connected:
                    continue
                augmented_events.extend(self._handle_button_change(event.button, is_pressed=True, source="joystick"))
                continue

            if event.type == pygame.JOYBUTTONUP:
                self.last_input_source = "controller"
                self.mouse_visible = False
                if self.controllers or self._xinput_connected:
                    continue
                augmented_events.extend(self._handle_button_change(event.button, is_pressed=False, source="joystick"))
                continue

            if event.type == pygame.JOYHATMOTION:
                self.last_input_source = "controller"
                self.mouse_visible = False
                augmented_events.extend(self._handle_hat_motion(event.value))
                continue

            if event.type == pygame.JOYAXISMOTION:
                self.last_input_source = "controller"
                self.mouse_visible = False
                self._update_axis_vector()

        augmented_events.extend(self._poll_controller_state())
        augmented_events.extend(self._poll_analog_navigation())
        return augmented_events

    def get_movement_vector(self) -> Vector2:
        keys = pygame.key.get_pressed()
        keyboard = Vector2(0, 0)

        if keys[PLAYER_LEFT] or keys[pygame.K_LEFT]:
            keyboard.x -= 1
        if keys[PLAYER_RIGHT] or keys[pygame.K_RIGHT]:
            keyboard.x += 1
        if keys[PLAYER_UP] or keys[pygame.K_UP]:
            keyboard.y -= 1
        if keys[PLAYER_DOWN] or keys[pygame.K_DOWN]:
            keyboard.y += 1

        direction = keyboard + self.get_controller_vector()
        if direction.length_squared() > 1:
            direction = direction.normalize()
        return direction

    def get_controller_vector(self) -> Vector2:
        direction = self.dpad_vector + self.axis_vector
        if direction.length_squared() > 1:
            direction = direction.normalize()
        return direction

    def has_controller(self) -> bool:
        return False

    def apply_mouse_visibility(self):
        pygame.mouse.set_visible(self.mouse_visible)

    def set_virtual_mouse_position(self, pos: tuple[int, int]):
        self._virtual_mouse_target = (int(pos[0]), int(pos[1]))
        pygame.mouse.set_pos(self._virtual_mouse_target)

    def is_action_just_pressed(self, action: str) -> bool:
        return action in self.just_pressed_actions

    def is_key_just_pressed(self, key: int) -> bool:
        return key in self.just_pressed_keys

    def get_prompt_button(self, action: str) -> str:
        if self.last_input_source == "controller":
            labels = self._controller_action_labels_by_layout.get(
                self.controller_layout,
                self._controller_action_labels_by_layout["xbox"],
            )
        else:
            labels = self._keyboard_action_labels
        label = labels.get(action, action.upper())
        if action == "open_editor" and self.last_input_source != "controller":
            return LanguageService.get().get_ui_label("core_button")
        return label

    def get_prompt_items(self, context: str) -> list[tuple[str, str]]:
        language = LanguageService.get()
        if context == "menu":
            if self.last_input_source == "controller":
                return [
                    ("D-PAD", language.get_prompt_text("navigate")),
                    (self.get_prompt_button("confirm"), language.get_prompt_text("confirm")),
                    (self.get_prompt_button("back"), language.get_prompt_text("back")),
                ]
            return [("W/S", language.get_prompt_text("navigate")), ("ENTER", language.get_prompt_text("confirm")), ("ESC", language.get_prompt_text("back"))]
        if context == "help":
            if self.last_input_source == "controller":
                return [("D-PAD", language.get_prompt_text("scroll")), (self.get_prompt_button("back"), language.get_prompt_text("back"))]
            return [("W/S", language.get_prompt_text("scroll")), ("PGUP", language.get_prompt_text("up")), ("PGDN", language.get_prompt_text("down")), ("ESC", language.get_prompt_text("back"))]
        if context == "generic_level":
            if self.last_input_source == "controller":
                return [
                    (self.get_prompt_button("bomb"), language.get_prompt_text("bomb")),
                    (self.get_prompt_button("open_editor"), language.get_prompt_text("editor")),
                    (self.get_prompt_button("help"), language.get_prompt_text("help")),
                    (self.get_prompt_button("pause"), language.get_prompt_text("menu")),
                ]
            return [("B", language.get_prompt_text("bomb")), (self.get_prompt_button("open_editor"), language.get_prompt_text("editor")), ("F1", language.get_prompt_text("help")), ("ESC", language.get_prompt_text("menu"))]
        if context == "basic_level":
            if self.last_input_source == "controller":
                return [(self.get_prompt_button("help"), language.get_prompt_text("help")), (self.get_prompt_button("pause"), language.get_prompt_text("menu"))]
            return [("F1", language.get_prompt_text("help")), ("ESC", language.get_prompt_text("menu"))]
        if context == "home":
            if self.last_input_source == "controller":
                return [
                    (self.get_prompt_button("pause"), language.get_prompt_text("menu")),
                    (self.get_prompt_button("help"), language.get_prompt_text("help")),
                ]
            return [("ESC", language.get_prompt_text("menu")), ("F1", language.get_prompt_text("help"))]
        if context == "circuit_editor":
            if self.last_input_source == "controller":
                return [
                    (self.get_prompt_button("help"), language.get_prompt_text("menu_grid")),
                    ("D-PAD/L", language.get_prompt_text("move")),
                    (self.get_prompt_button("confirm"), language.get_prompt_text("apply")),
                    (self.get_prompt_button("bomb"), language.get_prompt_text("wire")),
                    (self.get_prompt_button("open_editor"), language.get_prompt_text("rotate_select")),
                    (self.get_prompt_button("tool_prev"), language.get_prompt_text("tool_prev")),
                    (self.get_prompt_button("tool_next"), language.get_prompt_text("tool_next")),
                    (self.get_prompt_button("back"), language.get_prompt_text("cancel")),
                    (self.get_prompt_button("pause"), language.get_prompt_text("exit")),
                ]
            return [("MOUSE", language.get_prompt_text("cursor")), ("N/W/G", language.get_prompt_text("tools")), ("R/S/DEL", language.get_prompt_text("edit")), ("ESC", language.get_prompt_text("cancel"))]
        if context == "circuit_editor_grid":
            return [
                ("D-PAD/L", language.get_prompt_text("move")),
                (self.get_prompt_button("confirm"), language.get_prompt_text("apply")),
                (self.get_prompt_button("open_editor"), language.get_prompt_text("rotate_select")),
                (self.get_prompt_button("back"), language.get_prompt_text("cancel")),
                (self.get_prompt_button("tool_prev"), language.get_prompt_text("tool_prev")),
                (self.get_prompt_button("tool_next"), language.get_prompt_text("tool_next")),
                (self.get_prompt_button("menu_confirm"), language.get_prompt_text("click_menu")),
                (self.get_prompt_button("pause"), language.get_prompt_text("exit")),
            ]
        return []

    def _connect_joystick(self, device_index: int):
        try:
            joystick = pygame.joystick.Joystick(device_index)
            joystick.init()
        except pygame.error:
            return
        self.joysticks[joystick.get_instance_id()] = joystick
        self.controller_layout = self._detect_layout_from_name(joystick.get_name())
        self._prev_button_states = {
            button_index: False for button_index in range(joystick.get_numbuttons())
        }
        self._prev_hat_value = (0, 0)
        self._update_axis_vector()

    def _connect_controllers(self):
        if sdl2_controller is None:
            return
        try:
            count = sdl2_controller.get_count()
        except Exception:
            return

        self.controllers.clear()
        for device_index in range(count):
            try:
                controller = sdl2_controller.Controller(device_index)
                controller.init()
                self.controllers[controller.id] = controller
                self.controller_layout = self._detect_layout_from_name(controller.name)
            except Exception:
                continue

    def _disconnect_joystick(self, instance_id: int):
        joystick = self.joysticks.pop(instance_id, None)
        if joystick is not None:
            joystick.quit()
        self.axis_vector.xy = 0, 0
        self.dpad_vector.xy = 0, 0
        self._pressed_virtual_keys.clear()
        self._pressed_actions.clear()
        self._prev_button_states.clear()
        self._prev_hat_value = (0, 0)
        if not self.joysticks:
            self.controller_layout = "xbox"

    def _detect_layout_from_name(self, name: str) -> str:
        normalized = name.lower()
        if any(token in normalized for token in ("sony", "playstation", "dualshock", "dualsense", "wireless controller")):
            return "playstation"
        return "xbox"

    def _button_actions_for_source(self, source: str, button: int) -> tuple[str, ...]:
        if source == "sdl2":
            return self._button_to_actions_sdl2.get(button, ())
        if source == "xinput":
            return self._button_to_actions_xinput.get(button, ())
        return self._button_to_actions_joystick.get(button, ())

    def _handle_button_change(self, button: int, is_pressed: bool, source: str = "joystick") -> list[pygame.event.Event]:
        actions = self._button_actions_for_source(source, button)
        synthetic_events: list[pygame.event.Event] = []

        for action in actions:
            if is_pressed:
                self.just_pressed_actions.add(action)
                self._pressed_actions.add(action)
            else:
                self._pressed_actions.discard(action)

            for key in self._action_to_keys.get(action, ()):
                event = self._set_virtual_key_state(key, is_pressed)
                if event is not None:
                    synthetic_events.append(event)

        return synthetic_events

    def _handle_hat_motion(self, value: tuple[int, int]) -> list[pygame.event.Event]:
        new_vector = Vector2(value[0], -value[1])
        keys_by_direction = {
            "left": (pygame.K_LEFT,),
            "right": (pygame.K_RIGHT,),
            "up": (pygame.K_UP,),
            "down": (pygame.K_DOWN,),
        }
        previous = {
            "left": self.dpad_vector.x < 0,
            "right": self.dpad_vector.x > 0,
            "up": self.dpad_vector.y < 0,
            "down": self.dpad_vector.y > 0,
        }
        current = {
            "left": new_vector.x < 0,
            "right": new_vector.x > 0,
            "up": new_vector.y < 0,
            "down": new_vector.y > 0,
        }

        self.dpad_vector = new_vector
        synthetic_events: list[pygame.event.Event] = []

        for direction, pressed_now in current.items():
            if previous[direction] == pressed_now:
                continue
            for key in keys_by_direction[direction]:
                event = self._set_virtual_key_state(key, pressed_now)
                if event is not None:
                    synthetic_events.append(event)

        return synthetic_events

    def _update_axis_vector(self):
        self.axis_vector.xy = 0, 0
        if self._xinput_connected and self._xinput_state is not None:
            gamepad = self._xinput_state.Gamepad
            axis_x = self._normalize_thumb_axis(gamepad.sThumbLX)
            axis_y = self._normalize_thumb_axis(gamepad.sThumbLY)
            axis_y = -axis_y
        else:
            controller = self._get_primary_controller()
            if controller is not None:
                try:
                    axis_x = float(controller.get_axis(0)) / 32767.0
                    axis_y = float(controller.get_axis(1)) / 32767.0
                except Exception:
                    axis_x = 0.0
                    axis_y = 0.0
            elif self.joysticks:
                joystick = next(iter(self.joysticks.values()))
                axis_x = joystick.get_axis(0) if joystick.get_numaxes() > 0 else 0.0
                axis_y = joystick.get_axis(1) if joystick.get_numaxes() > 1 else 0.0
            else:
                return

        self.axis_vector.x = axis_x if abs(axis_x) >= self.deadzone else 0.0
        self.axis_vector.y = axis_y if abs(axis_y) >= self.deadzone else 0.0

    def _refresh_connected_joysticks(self):
        if not pygame.joystick.get_init():
            pygame.joystick.init()
        detected_count = pygame.joystick.get_count()
        if detected_count == len(self.joysticks):
            self._connect_controllers()
            return

        known_ids = set(self.joysticks.keys())
        current_ids = set()
        for device_index in range(detected_count):
            try:
                joystick = pygame.joystick.Joystick(device_index)
                joystick.init()
                current_ids.add(joystick.get_instance_id())
                if joystick.get_instance_id() not in known_ids:
                    self.joysticks[joystick.get_instance_id()] = joystick
                    self.controller_layout = self._detect_layout_from_name(joystick.get_name())
            except pygame.error:
                continue

        for instance_id in list(self.joysticks.keys()):
            if instance_id not in current_ids:
                self._disconnect_joystick(instance_id)
        self._connect_controllers()
        self._poll_xinput_state()

    def _poll_controller_state(self) -> list[pygame.event.Event]:
        synthetic_events: list[pygame.event.Event] = []
        self._poll_xinput_state()
        if not self.joysticks and not self.controllers and not self._xinput_connected:
            self.axis_vector.xy = 0, 0
            self.dpad_vector.xy = 0, 0
            return synthetic_events

        controller = self._get_primary_controller()
        if self._xinput_connected:
            self.controller_layout = "xbox"
        elif controller is not None:
            self.controller_layout = self._detect_layout_from_name(controller.name)
        elif self.joysticks:
            joystick = next(iter(self.joysticks.values()))
            self.controller_layout = self._detect_layout_from_name(joystick.get_name())
        else:
            self.controller_layout = "xbox"
        self._update_axis_vector()

        if self.axis_vector.length_squared() > 0:
            self.last_input_source = "controller"
            self.mouse_visible = False

        if self._xinput_connected:
            button_count = 10
        elif controller is not None:
            button_count = 15
        elif self.joysticks:
            joystick = next(iter(self.joysticks.values()))
            button_count = joystick.get_numbuttons()
        else:
            button_count = 0
        if len(self._prev_button_states) != button_count:
            self._prev_button_states = {
                button_index: False for button_index in range(button_count)
            }

        for button_index in range(button_count):
            source = "joystick"
            if self._xinput_connected:
                pressed_now = self._xinput_button_pressed(button_index)
                source = "xinput"
            elif controller is not None:
                try:
                    pressed_now = bool(controller.get_button(button_index))
                    source = "sdl2"
                except Exception:
                    pressed_now = False
            elif self.joysticks:
                pressed_now = bool(joystick.get_button(button_index))
            else:
                pressed_now = False
            pressed_before = self._prev_button_states.get(button_index, False)
            if pressed_now != pressed_before:
                self.last_input_source = "controller"
                self.mouse_visible = False
                synthetic_events.extend(
                    self._handle_button_change(button_index, is_pressed=pressed_now, source=source)
                )
                self._prev_button_states[button_index] = pressed_now

        if self._xinput_connected:
            hat_value = self._xinput_hat_value()
        elif controller is not None:
            hat_value = (
                int(bool(controller.get_button(14))) - int(bool(controller.get_button(13))),
                int(bool(controller.get_button(11))) - int(bool(controller.get_button(12))),
            )
        elif self.joysticks:
            hat_value = joystick.get_hat(0) if joystick.get_numhats() > 0 else (0, 0)
        else:
            hat_value = (0, 0)
        if hat_value != self._prev_hat_value:
            self.last_input_source = "controller"
            self.mouse_visible = False
            synthetic_events.extend(self._handle_hat_motion(hat_value))
            self._prev_hat_value = hat_value

        return synthetic_events

    def _poll_analog_navigation(self) -> list[pygame.event.Event]:
        synthetic_events: list[pygame.event.Event] = []
        threshold = 0.55
        current = {
            "left": self.axis_vector.x <= -threshold,
            "right": self.axis_vector.x >= threshold,
            "up": self.axis_vector.y <= -threshold,
            "down": self.axis_vector.y >= threshold,
        }
        keys_by_direction = {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
        }

        for direction, pressed_now in current.items():
            pressed_before = self._prev_axis_digital[direction]
            if pressed_now == pressed_before:
                continue
            self._prev_axis_digital[direction] = pressed_now
            self.last_input_source = "controller"
            self.mouse_visible = False
            event = self._set_virtual_key_state(keys_by_direction[direction], pressed_now)
            if event is not None:
                synthetic_events.append(event)

        return synthetic_events

    def _get_primary_controller(self):
        if not self.controllers:
            return None
        return next(iter(self.controllers.values()))

    def _load_xinput(self):
        if not hasattr(ctypes, "windll"):
            return None
        for dll_name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
            try:
                return ctypes.windll.LoadLibrary(dll_name)
            except Exception:
                continue
        return None

    def _poll_xinput_state(self):
        if self._xinput is None:
            self._xinput_connected = False
            self._xinput_state = None
            return
        self._xinput_connected = False
        self._xinput_state = None
        for slot in range(4):
            state = XINPUT_STATE()
            result = self._xinput.XInputGetState(slot, ctypes.byref(state))
            if result == 0:
                self._xinput_connected = True
                self._xinput_state = state
                return

    def _normalize_thumb_axis(self, raw_value: int) -> float:
        if raw_value >= 0:
            return min(1.0, raw_value / 32767.0)
        return max(-1.0, raw_value / 32768.0)

    def _xinput_button_pressed(self, button_index: int) -> bool:
        if not self._xinput_connected or self._xinput_state is None:
            return False
        bitmask_map = {
            0: 0x1000,
            1: 0x2000,
            2: 0x4000,
            3: 0x8000,
            4: 0x0100,
            5: 0x0200,
            6: 0x0020,
            7: 0x0010,
            8: 0x0040,
            9: 0x0080,
        }
        mask = bitmask_map.get(button_index)
        if mask is None:
            return False
        return bool(self._xinput_state.Gamepad.wButtons & mask)

    def _xinput_hat_value(self) -> tuple[int, int]:
        if not self._xinput_connected or self._xinput_state is None:
            return (0, 0)
        buttons = self._xinput_state.Gamepad.wButtons
        x = int(bool(buttons & 0x0008)) - int(bool(buttons & 0x0004))
        y = int(bool(buttons & 0x0001)) - int(bool(buttons & 0x0002))
        return (x, y)

    def _set_virtual_key_state(self, key: int, is_pressed: bool):
        if is_pressed:
            if key in self._pressed_virtual_keys:
                return None
            self._pressed_virtual_keys.add(key)
            self.just_pressed_keys.add(key)
            return pygame.event.Event(pygame.KEYDOWN, key=key, synthetic_controller=True)

        if key not in self._pressed_virtual_keys:
            return None
        self._pressed_virtual_keys.remove(key)
        return pygame.event.Event(pygame.KEYUP, key=key, synthetic_controller=True)


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]
