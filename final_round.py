from datetime import datetime
from util import green, red, wait_for_choice

class FinalRound :

    def __init__(self, questions) :
        self.questions = questions
        self.round_bank = 0
        self.num_rounds = 5
        self.started = False

    def start_round(self, players, first_player) :
        if self.started :
            print('Round is already started!')
            return
        self.players = players
        self.started = True
        self.start_time = datetime.now()
        self.question_start_time = self.start_time
        self.current_question = 0

        self.first_player_offset = 0
        for player in players :
            if first_player == player :
                break
            else :
                self.first_player_offset += 1

        self.run()

    def run(self) :
        # TODO if so-and-so gets this one correct they win
        # TODO so-and-so must get this one correct to stay in the game
        current_question = 0
        scores = [[] for player in self.players]
        for current_question in range(0, self.num_rounds * 2) :
            player_num = (current_question + self.first_player_offset) % len(self.players)
            current_player = self.players[player_num]
            (question, answer) = self.questions.get_next_question()
            print(green('"' + current_player + ': ' + question + '?"') + ' (Answer: ' +  red(answer) + ')')
            choice = wait_for_choice("[Z]tupid or [C]orrect ? ", ['c', 'z']).lower()
            scores[player_num].append(1 if choice == 'c' else 0)
            self.print_score_update(scores)

        # Sum the totals
        final_scores = [sum(score) for score in scores]

        if final_scores[0] == final_scores[1] :
            print('There was a Tie! Sudden death!')
            self.winner = self.sudden_death(scores)
        elif final_scores[0] < final_scores[1] :
            self.winner = self.players[1]
        else :
            self.winner = self.players[0]

    def print_score_update(self, scores) :
        print('Scores:')
        for (player, score) in zip(self.players, scores) :
            print(player, end=':')
            for s in score :
                if s == 0 :
                    print(' ❌', end='')
                else :
                    print(' ✅', end='')
            for _ in range(len(score), self.num_rounds) :
                print(' -', end='')
            print()
        print()

    def sudden_death(self, scores) :
        for current_question in range(10, self.questions.remaining_questions()) :
            player_num = (current_question + self.first_player_offset) % len(self.players)
            current_player = self.players[player_num]
            (question, answer) = self.questions.get_next_question()
            print(green('"' + current_player + ': ' + question + '?"') + ' (Answer: ' +  red(answer) + ')')
            choice = wait_for_choice("[Z]tupid or [C]orrect ? ", ['c', 'z']).lower()
            scores[player_num].append(1 if choice == 'c' else 0)
            self.print_score_update(scores)

            if len(scores[0]) == len(scores[1]) :
                final_scores = [sum(score) for score in scores]
                if final_scores[0] < final_scores[1] :
                    return self.players[1]
                elif final_scores[0] > final_scores[1] :
                    return self.players[0]
        return 'No one'
