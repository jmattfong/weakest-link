from util import wait_for_choice, green, red, dollars, random_mean_word, starts_with_vowel

class WeakestLinkGame :

    def __init__(self, players, rounds, final_round) :
        self.players = players
        self.rounds = rounds
        self.final_round = final_round
        self.total_bank = 0
        self.maximum_bank = 0
        self.current_round = 0

    def get_current_round(self) :
        return self.rounds[self.current_round] if self.current_round < len(self.rounds) else self.final_round

    def run(self) :
        first_player = self.players[0]
        for i in range(len(self.rounds)) :
            self.current_round = i
            if len(self.players) == 2 :
                print("Not running all rounds since we don't have enough players")
                print()
                break
            if i != 0 :
                print('As the strongest link last round,', green(first_player), 'will go first')
                print()
            round = self.rounds[i]
            self.try_to_start_round(i+1, round, first_player)
            first_player = self.handle_finished_round_results(round)
            weakest_link = self.vote_for_weakest_link()
            if first_player == weakest_link :
                first_player = round.get_strongest_link(first_player)

        while len(self.players) > 2 :
            weakest_link = self.vote_for_weakest_link()
            if first_player == weakest_link :
                first_player = round.get_strongest_link(first_player)

        first_player = wait_for_choice('As the strongest link last round, ' + green(first_player) + ' chooses who will go first in the ' +\
                            red('final round') + '. Choices: ' + ", ".join(self.players) + ' > ', self.players)

        self.try_to_start_round('Final', self.final_round, first_player)
        print(green(str(self.final_round.winner) + ' is the winner! They win ' + dollars(self.total_bank)))
        print()
        print("Game over, goodnight!")

    def try_to_start_round(self, round_num, round, first_player) :
        wait_for_choice("Enter 'S' to start round " + str(round_num) + " > ", 'S')
        print('Starting round', round_num)
        print()

        round.start_round(self.players, first_player)

        print('Finished round', round_num)
        print()

    def handle_finished_round_results(self, round) :
        # TODO determine next first player and total bank
        self.total_bank += round.round_bank
        self.maximum_bank += round.bank_links[-1]
        strongest_link = round.get_strongest_link()
        print('That round the team banked', dollars(round.round_bank))
        adjective = random_mean_word()
        print('Out of a possible', dollars(self.maximum_bank), "the team banked", 'an' if starts_with_vowel(adjective) else 'a', adjective, dollars(self.total_bank))
        print('Statistically, the strongest link was', green(strongest_link))
        print('Statistically, the weakest link was', red(round.get_weakest_link()))
        print()
        return strongest_link

    def vote_for_weakest_link(self) :
        weakest_link = wait_for_choice("Who is the weakest link? Choices: " + ', '.join(self.players) + " > ", self.players)
        self.players.remove(weakest_link)
        return weakest_link
