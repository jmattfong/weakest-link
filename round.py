import threading
from datetime import datetime

from util import debug, green, red, wait_for_choice

class WeakestLinkRound :

    def __init__(self, round_time_s, bank_links, questions) :
        self.round_time_s = round_time_s
        self.bank_links = bank_links
        self.questions = questions
        self.round_bank = 0
        self.current_link = 0
        self.started = False
        self.spaces = '                                '
        self.players = []
        self.current_question = 0
        self.current_player_banked = 0
        self.first_player_offset = 0
        self.seconds_remaining = self.round_time_s

    def start_round(self, players, first_player) :
        if self.started :
            print('Round is already started!')
            return
        self.players = players
        self.player_answers = dict([(player, []) for player in players])
        self.start_time = datetime.now()
        self.question_start_time = self.start_time
        self.started = True

        self.first_player_offset = 0
        for player in players :
            if first_player == player :
                break
            else :
                self.first_player_offset += 1

        self.run()

    def start_timer(self) :
        self.seconds_remaining = self.round_time_s
        self.done = False
        self.timer()

    def timer(self) :
        if self.done :
            self.stop_round()
            return
        if self.seconds_remaining < 1200 :
            seconds = str(self.seconds_remaining)
            while len(seconds) < 3 :
                seconds = ' ' + seconds
            print('\r', seconds, 'seconds remaining', end ="")
        self.seconds_remaining -= 1
        if self.seconds_remaining >= 0:
            threading.Timer(1, self.timer).start()
        else :
            self.stop_round()

    def run(self) :
        self.start_timer()

        while not self.done :
            if self.current_link == len(self.bank_links) :
                self.bank()
                print(green('The team ran the chain!'))
                print()
                self.stop_round()
                return
            print(self.spaces, self.get_question(), end ="")
            choice = wait_for_choice("\r" + self.spaces[:-7] + "[Z,X,C] ", ['c', 'z', 'x']).lower()
            if self.done :
                print('Round is over!')
                break
            elif choice == 'c' :
                self.answer_question(True)
            elif choice == 'z':
                self.answer_question(False)
            else:
                self.current_player_banked = self.bank()

        self.done = True
        print()

    def get_current_player_num(self) :
        return (self.current_question + self.first_player_offset) % len(self.players) if len(self.players) > 0 else 0

    def get_current_player(self) :
        return self.players[self.get_current_player_num()]

    def get_question(self) :
        current_player = self.get_current_player()
        (question, answer) = self.questions.get_next_question()
        return green('"' + current_player + ': ' + question + '?"') + ' (Answer: ' +  red(answer) + ')'

    def bank(self) :
        if not self.started :
            print('Round is over!')
            return 0

        if self.current_link == 0 :
            print(self.spaces, 'No BANK. Total this round:', self.round_bank)
            return 0
        # TODO handle win condition or else get IndexError because we ran off the end of the chain
        amount_banked = self.bank_links[self.current_link - 1]
        self.round_bank += amount_banked
        self.current_link = 0

        print(self.spaces, 'Recorded BANK. Total this round:', self.round_bank)

        return amount_banked

    def answer_question(self, correct) :
        if not self.started :
            print('Round is over!')
            return
        question_stop_time = datetime.now()
        # TODO why was it like this? current_player = self.players[self.current_question % len(self.players)]
        current_player = self.get_current_player()
        answer = (correct, question_stop_time - self.question_start_time, self.current_player_banked)
        self.player_answers[current_player].append(answer)

        # Setup the next question
        self.current_player_banked = 0
        if correct :
            self.current_link += 1
        else :
            self.current_link = 0
        self.question_start_time = question_stop_time
        self.current_question += 1

        print(self.spaces, 'Recorded', 'CORRECT' if correct else 'INCORRECT', 'answer')
        debug(current_player, 'answered', answer)

    def stop_round(self) :
        self.started = False
        self.done = True
        print()

    def get_strongest_link(self, eliminated=None) :
        strongest_link = None
        for (player, answers) in self.player_answers.items() :
            if player == eliminated :
                continue
            total_correct = 0
            total_time = 0
            total_banked = 0
            for (correct, time_taken, money_banked) in answers :
                total_correct += correct
                total_time = total_time + time_taken.total_seconds()
                total_banked += money_banked

            percent_correct = float(total_correct) / len(answers) if len(answers) > 0 else 0

            if strongest_link == None :
                strongest_link = (player, percent_correct, total_time, total_banked)
            else :
                (strongest_player, strongest_percent, strongest_time, strongest_banked) = strongest_link

                if percent_correct > strongest_percent :
                    strongest_link = (player, percent_correct, total_time, total_banked)
                    debug(player, 'has a better percent correct with', percent_correct, 'than', strongest_player, 'with', strongest_percent)
                elif percent_correct == strongest_percent :
                    if total_banked > strongest_banked :
                        strongest_link = (player, percent_correct, total_time, total_banked)
                        debug(player, 'has banked more with', total_banked, 'than', strongest_player, 'with', strongest_banked)
                    elif total_banked == strongest_banked :
                        if total_time < strongest_time :
                            strongest_link = (player, percent_correct, total_time, total_banked)
                            debug(player, 'took less time', total_time, 'than', strongest_player, 'with', strongest_time)
                        elif total_time == strongest_time :
                            print('Holy crap, a strongest link tie between', player, 'and', strongest_player)

        (strongest_player, strongest_percent, strongest_time, strongest_banked) = strongest_link
        return strongest_player


    def get_weakest_link(self) :
        weakest_link = None
        for (player, answers) in self.player_answers.items() :
            total_correct = 0
            total_time = 0
            total_banked = 0
            for (correct, time_taken, money_banked) in answers :
                total_correct += correct
                total_time = total_time + time_taken.total_seconds()
                total_banked += money_banked

            percent_correct = float(total_correct) / len(answers) if len(answers) > 0 else 0

            if weakest_link == None :
                weakest_link = (player, percent_correct, total_time, total_banked)
            else :
                (weakest_player, weakest_percent, weakest_time, weakest_banked) = weakest_link

                if percent_correct < weakest_percent :
                    weakest_link = (player, percent_correct, total_time, total_banked)
                    debug(player, 'had a worse percent correct with', percent_correct, 'than', weakest_player, 'with', weakest_percent)
                elif percent_correct == weakest_percent :
                    if total_banked < weakest_banked :
                        weakest_link = (player, percent_correct, total_time, total_banked)
                        debug(player, 'has banked less with', total_banked, 'than', weakest_player, 'with', weakest_banked)
                    elif total_banked == weakest_banked :
                        if total_time > weakest_time :
                            weakest_link = (player, percent_correct, total_time, total_banked)
                            debug(player, 'took more time', total_time, 'than', weakest_player, 'with', weakest_time)
                        elif total_time == weakest_time :
                            print('Holy crap, a weakest link tie between', player, 'and', weakest_player)

        (weakest_player, weakest_percent, weakest_time, weakest_banked) = weakest_link
        return weakest_player
