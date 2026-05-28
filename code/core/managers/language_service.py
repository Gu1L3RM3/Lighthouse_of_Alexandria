from core.settings import DEFAULT_LANGUAGE
from core.repositories.language_preferences_repository import LanguagePreferencesRepository


class LanguageService:
    _instance = None
    SUPPORTED_LANGUAGES = ("en", "pt-BR")
    SYSTEM_LABELS = {
        "en": {
            "window_title": "Lighthouse of Alexandria",
        },
        "pt-BR": {
            "window_title": "Farol de Alexandria",
        },
    }
    MENU_LABELS = {
        "en": {
            "resume_initial": "RESUME LEVEL",
            "resume_continue": "CONTINUE JOURNEY",
            "resume_empty": "NO SAVE AVAILABLE",
            "start": "NEW JOURNEY",
            "credits": "CREDITS",
            "exit": "EXIT",
            "language_button": "EN / PT-BR",
            "title_line1": "LIGHTHOUSE OF",
            "title_line2": "ALEXANDRIA",
            "title_subtitle": "Story, puzzles and electricity",
            "title_tagline": "pixel adventure",
        },
        "pt-BR": {
            "resume_initial": "RETOMAR FASE",
            "resume_continue": "CONTINUAR JORNADA",
            "resume_empty": "SEM SAVE ATIVO",
            "start": "INICIAR JORNADA",
            "credits": "CREDITOS",
            "exit": "SAIR",
            "language_button": "PT-BR / EN",
            "title_line1": "FAROL DE",
            "title_line2": "ALEXANDRIA",
            "title_subtitle": "Historia, enigmas e eletricidade",
            "title_tagline": "aventura pixel",
        },
    }
    UI_LABELS = {
        "en": {
            "top_menu": "MENU",
            "top_help": "HELP",
            "help_back": "BACK",
            "core_button": "CORE",
            "enter": "ENTER",
            "interact": "INTERACT",
            "talk": "TALK",
            "read": "READ",
            "open": "OPEN",
            "bomb_status_title": "CORES",
            "bomb_status_fallback": "STANDARD",
            "bomb_status_time": "Time",
            "bomb_status_area": "Area",
            "bomb_status_pulse": "Pulse",
            "editor_node": "Node",
            "editor_v_source": "V Source",
            "editor_resistor": "Resistor",
            "editor_i_source": "I Source",
            "editor_gnd": "GND",
            "editor_wire": "Wire",
            "editor_solve": "Solve",
            "editor_load": "Load",
            "editor_clear": "Clear",
            "editor_close": "X",
            "panel_label": "PANEL",
        },
        "pt-BR": {
            "top_menu": "MENU",
            "top_help": "AJUDA",
            "help_back": "VOLTAR",
            "core_button": "NUCLEO",
            "enter": "ENTRAR",
            "interact": "INTERAGIR",
            "talk": "CONVERSAR",
            "read": "LER",
            "open": "ABRIR",
            "bomb_status_title": "NUCLEOS",
            "bomb_status_fallback": "PADRAO",
            "bomb_status_time": "Tempo",
            "bomb_status_area": "Area",
            "bomb_status_pulse": "Pulso",
            "editor_node": "No",
            "editor_v_source": "Fonte V",
            "editor_resistor": "Resistor",
            "editor_i_source": "Fonte I",
            "editor_gnd": "GND",
            "editor_wire": "Fio",
            "editor_solve": "Resolver",
            "editor_load": "Carregar",
            "editor_clear": "Limpar",
            "editor_close": "X",
            "panel_label": "PAINEL",
        },
    }
    PROMPT_TEXTS = {
        "en": {
            "navigate": "navigate",
            "confirm": "confirm",
            "back": "back",
            "scroll": "scroll",
            "up": "up",
            "down": "down",
            "bomb": "bomb",
            "editor": "editor",
            "help": "help",
            "menu": "menu",
            "move": "move",
            "apply": "apply",
            "wire": "wire",
            "rotate_select": "rotate/select",
            "tool_prev": "tool-",
            "tool_next": "tool+",
            "cancel": "cancel",
            "exit": "exit",
            "close": "close",
            "cursor": "cursor",
            "tools": "tools",
            "edit": "edit",
            "menu_grid": "menu/grid",
            "click_menu": "click menu",
        },
        "pt-BR": {
            "navigate": "navegar",
            "confirm": "confirmar",
            "back": "voltar",
            "scroll": "rolar",
            "up": "subir",
            "down": "descer",
            "bomb": "bomba",
            "editor": "editor",
            "help": "ajuda",
            "menu": "menu",
            "move": "mover",
            "apply": "aplicar",
            "wire": "fio",
            "rotate_select": "girar/selecionar",
            "tool_prev": "ferramenta-",
            "tool_next": "ferramenta+",
            "cancel": "cancelar",
            "exit": "sair",
            "close": "fechar",
            "cursor": "cursor",
            "tools": "ferramentas",
            "edit": "editar",
            "menu_grid": "menu/grid",
            "click_menu": "clicar menu",
        },
    }

    def __init__(self, repository: LanguagePreferencesRepository | None = None):
        self.repository = repository or LanguagePreferencesRepository()
        self.current_language = self._normalize_language(self.repository.load_language())

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = LanguageService()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def _normalize_language(self, language: str | None) -> str:
        if language in self.SUPPORTED_LANGUAGES:
            return language
        return DEFAULT_LANGUAGE

    def get_current_language(self) -> str:
        return self.current_language

    def set_language(self, language: str) -> str:
        normalized = self._normalize_language(language)
        self.current_language = normalized
        self.repository.save_language(normalized)
        return normalized

    def toggle_language(self) -> str:
        next_language = "pt-BR" if self.current_language == "en" else "en"
        return self.set_language(next_language)

    def get_menu_label(self, key: str) -> str:
        labels = self.MENU_LABELS.get(self.current_language, self.MENU_LABELS[DEFAULT_LANGUAGE])
        return labels.get(key, key)

    def get_system_label(self, key: str) -> str:
        labels = self.SYSTEM_LABELS.get(self.current_language, self.SYSTEM_LABELS[DEFAULT_LANGUAGE])
        return labels.get(key, key)

    def get_ui_label(self, key: str) -> str:
        labels = self.UI_LABELS.get(self.current_language, self.UI_LABELS[DEFAULT_LANGUAGE])
        return labels.get(key, key)

    def get_prompt_text(self, key: str) -> str:
        labels = self.PROMPT_TEXTS.get(self.current_language, self.PROMPT_TEXTS[DEFAULT_LANGUAGE])
        return labels.get(key, key)
