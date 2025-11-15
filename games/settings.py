class Settings:
    def __init__(self):
        self.games_enabled = {
            "song": True,
            "human_animal_plant": True,
            "compatibility": True,
            "chain_words": True,
            "differences": True,
            "letters_words": True,
            "fast_typing": True,
            "opposite": True
        }

    def enable_game(self, name):
        if name in self.games_enabled:
            self.games_enabled[name] = True

    def disable_game(self, name):
        if name in self.games_enabled:
            self.games_enabled[name] = False

    def is_enabled(self, name):
        return self.games_enabled.get(name, False)
