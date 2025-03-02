from dataclasses import dataclass, field
import sqlite3
from typing import ClassVar


@dataclass
class DataStore:
    # Instance Variables
    db_name: str
    conn: sqlite3.Connection = field(init=False)
    cursor: sqlite3.Cursor = field(init=False)

    # Class Variables
    n_past_states: ClassVar[int]

    def __post_init__(self) -> None:
        """Auto constructor to initialise the table if it doesn't and commit the changes."""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        # Create game state table if it doesn't exist
        _ = self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                life INTEGER NOT NULL,
                experience INTEGER NOT NULL,
                inputString TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Commiting and releasing the resources
        self.conn.commit()

    # Need to discuss about the fields and the data types of all the field with the rest of
    # the teams for applying database storage dtypes
    def save_game_state(self, player_name: str, life, experience) -> None:
        """Function saves the latest recorded game state."""

        # Sql query formula for populating game state
        _ = self.cursor.execute(
                """
                INSERT INTO game_state (player_name, life, experience, inputString)
                VALUES (?, ?, ?, ?)
                """, (player_name, life, experience)
            )

        # Commiting and releasing the resources
        self.conn.commit()

        """
        Logging (Need to check with Oliver for Scope): 
        print(f"Game status saved: {player_name} | life: {life} | experience: {experience} | input: {String}")
        """

    def load_game_state(self, player_name: str) -> list[tuple[str, ...]] | None:
        """Load the game status of the specified player upto n_past_states"""

        # Sql query formula for retreiving game states
        _ = self.cursor.execute(
            """
            SELECT life, experience, inputString, timestamp FROM game_state
            WHERE player_name = ?
            ORDER BY timestamp DESC LIMIT 1
            """, (player_name,)
        )
        result: list[tuple[str, ...]] = self.cursor.fetchall()

        if result:
            # life, experience, inputString, timestamp = result
            # print(f"Player {player_name} game status: life {life}, experience {experience}, 
            # input{inputString}, Time {timestamp}")
            return result
        else:
            print(f"Fail to find {player_name} game status")
            return None

    def delete_game_state(self, player_name: str) -> bool:
        """Delete a player's save"""
        _ = self.cursor.execute("DELETE FROM game_state WHERE player_name = ?", (player_name,))

        # Checking
        _ = self.cursor.execute("SELECT * FROM game_state WHERE player_name == ?", (player_name))
        search_player: list[tuple[str, ...]] = self.cursor.fetchall()
        if search_player:
            raise NotImplementedError
        else:
            return True
            # print(f"{player_name} save has been deleted")

    """Updating game states might not be necessary, will need to check against the"""
    # def update_game_state(self, player_name, new_life, new_experience, String):
    #     """Update players game status"""
    #     conn = sqlite3.connect("game_state.db")
    #     cursor = conn.cursor()

    #     _ = cursor.execute("""
    #         UPDATE game_state
    #         SET life = ?, experience = ?, inputString = ?, timestamp = CURRENT_TIMESTAMP
    #         WHERE player_name = ?
    #     """, (new_life, new_experience, String, player_name))

    #     conn.commit()
    #     conn.close()
    #     # print(f"{player_name} game status has been updated:life {new_life}, experience {new_experience}, input{String}")

    # def get_player_life(self, player_name):
    #     state = load_game_state(player_name)
    #     if state != None:
    #         life, experience, inputString, timestamp = state
    #         return life
    #     else:
    #         print("Fail to get the life")

    # Get experience of a player
    # def get_player_experience(player_name):
    #     state = load_game_state(player_name)
    #     if state != None:
    #         life, experience, inputString, timestamp = state
    #         return experience
    #     else:
    #         print("Fail to get the experience")

    """Purpose of this function ??????"""
    # Get input of a player
    # def get_player_input(player_name):
    #     state = load_game_state(player_name)
    #     if state != None:
    #         life, experience, inputString, timestamp = state
    #         return inputString
    #     else:
    #         print("Fail to get the input")
