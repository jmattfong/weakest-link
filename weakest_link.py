#!/usr/bin/env python3

from datetime import datetime, timedelta
import csv
import sys
import time
import threading
import random
import socketserver
import http.server
import re
import json

DEFAULT_DATA_PATH="data/"

# How much each default "dollar" is worth
DOLLAR_PERCENT = 1.0 / 2000

ROUND_1_LINKS = [
    1_000,
    2_000,
    3_000,
    4_000,
    5_000,
    7_500,
    10_000,
    25_000
]

ROUND_2_LINKS = [
    1_000,
    2_500,
    5_000,
    7_500,
    10_000,
    15_000,
    25_000,
    50_000
]

ROUND_3_LINKS = [
    1_000,
    2_500,
    5_000,
    7_500,
    10_000,
    25_000,
    50_000,
    75_000
]

ROUND_4_LINKS = [
    2_500,
    5_000,
    7_500,
    10_000,
    25_000,
    50_000,
    75_000,
    100_000
]

ROUND_5_LINKS = [
    2_500,
    5_000,
    10_000,
    25_000,
    50_000,
    75_000,
    100_000,
    250_000
]

ROUND_6_LINKS = [
    2_500,
    5_000,
    10_000,
    25_000,
    50_000,
    100_000,
    250_000,
    500_000
]

ROUNDS = [
    (150, ROUND_1_LINKS),
    (140, ROUND_2_LINKS),
    (130, ROUND_3_LINKS),
    (120, ROUND_4_LINKS),
    (110, ROUND_5_LINKS),
    (100, ROUND_6_LINKS)
]

GREEN = '\033[92m'
RED    = '\33[31m'
BOLD = '\033[1m'
END = '\033[0m'

DEBUG=False
def debug(*args) :
    if DEBUG :
        print('DEBUG:                          ', *args)
        print()

def wait_for_choice(message, choices) :
    input_val = ''
    lowercase_choices = [choice.lower() for choice in choices]
    while input_val.lower() not in lowercase_choices :
        input_val = input(message).strip()
    print()
    picked = [choice for choice in choices if input_val.lower() == choice.lower()]
    return picked[0]

def red(message) :
    return RED + BOLD + str(message) + END + END

def dollars(amount, color=True) :
    text = "${:,.2f}".format(amount)
    return green(text) if color else text

def format_time(seconds) :
    td = str(timedelta(seconds=seconds))
    return ':'.join(td.split(':')[1:])

def vowel_start(word) :
    return word[0].lower() in ['a', 'e', 'i', 'o', 'u']

def green(message) :
    return GREEN + BOLD + str(message) + END + END

def random_mean_word() :
    return random.choice([
        'paltry',
        'meager'
        'scanty',
        'miserable',
        'inadequate',
        'insufficient',
        'pathet ic',
        'stingy',
        'minute',
        'scaled-down',
        'mini',
        'pocket-sized',
        'fun-size',
        'petite',
        'miniature',
        'minuscule',
        'microscopic',
        'unhappy',
        'sorrowful',
        'regretful',
        'depressed',
        'downcast',
        'miserable',
        'sad',
        'upsetting',
        'shameful',
        'humiliating',
        'mortifying',
        'embarrassing',
    ])

class WeakestLinkRound :

    def __init__(self, round_time_s, bank_links, questions=None) :
        self.round_time_s = round_time_s
        self.bank_links = bank_links
        self.questions = questions if questions != None else []
        self.round_bank = 0
        self.current_link = 0
        self.started = False
        self.spaces = '                                '
        self.players = []
        self.current_question = 0
        self.current_player_banked = 0
        self.first_player_offset = 0
        self.seconds_remaining = self.round_time_s

    def add_question(self, question, answer) :
        self.questions.append((question, answer))

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

        while self.current_question < len(self.questions) and not self.done :
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
        (question, answer) = self.questions[self.current_question]
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

class FinalRound :

    # TODO copied init method
    def __init__(self, questions=[]) :
        self.questions = questions
        self.round_bank = 0
        self.num_rounds = 5
        self.started = False

    def add_question(self, question, answer) :
        self.questions.append((question, answer))

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
            (question, answer) = self.questions[current_question]
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
            for i in range(len(score), self.num_rounds) :
                print(' -', end='')
            print()
        print()

    def sudden_death(self, scores) :
        for current_question in range(10, len(self.questions)) :
            player_num = (current_question + self.first_player_offset) % len(self.players)
            current_player = self.players[player_num]
            (question, answer) = self.questions[current_question]
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
        print('Out of a possible', dollars(self.maximum_bank), "the team banked", 'an' if vowel_start(adjective) else 'a', adjective, dollars(self.total_bank))
        print('Statistically, the strongest link was', green(strongest_link))
        print('Statistically, the weakest link was', red(round.get_weakest_link()))
        print()
        return strongest_link

    def vote_for_weakest_link(self) :
        weakest_link = wait_for_choice("Who is the weakest link? Choices: " + ', '.join(self.players) + " > ", self.players)
        self.players.remove(weakest_link)
        return weakest_link

PORT=8080

def start_server():
    httpd = socketserver.ThreadingTCPServer(('', PORT), CustomHandler)
    httpd.serve_forever()

class CustomHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, directory='./html/', **kwargs) :
        super().__init__(*args, directory=directory, **kwargs)

    log_file = open('server.log', 'w', 1)
    def log_message(self, format, *args):
        self.log_file.write("%s - - [%s] %s\n" %
                            (self.client_address[0],
                             self.log_date_time_string(),
                             format%args))

    def do_GET(self):
        if None != re.search('/api/current-round', self.path):
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            response = {
                "players": game.players,
                "currentBank": dollars(game.get_current_round().round_bank, color=False),
                "totalBank": dollars(game.total_bank, color=False),
                "bankLinks": [dollars(link, color=False) for link in game.get_current_round().bank_links],
                "currentLink": game.get_current_round().current_link,
                "currentPlayer": game.get_current_round().get_current_player_num(),
                "time": format_time(game.get_current_round().seconds_remaining)
            }
            self.wfile.write(bytes(json.dumps(response), 'utf-8'))
        elif None != re.search('/api/final-round', self.path):
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(b"Final")
        else:
            # serve files, and directory listings by following self.path from ./html/ directory
            http.server.SimpleHTTPRequestHandler.do_GET(self)

t = threading.Thread(target=start_server)
print("Starting server at port", PORT)
print('Player view: \nhttp://localhost:' + str(PORT) + '/index.html')
print()
t.start()

question_file = sys.argv[1]
players = sys.argv[2:]
print('Welcome players', ', '.join(players))
print()

rounds = []
final_round = FinalRound()

with open(question_file) as csv_file:

    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader :
        round_num = int(row[0])
        question = row[1]
        answer = row[2]

        if round_num > len(ROUNDS) :
            final_round.add_question(question, answer)
        else :
            if round_num > len(rounds) :
                for i in range(len(rounds), round_num) :
                    (allotted_time, links) = ROUNDS[i]
                    links = [link * DOLLAR_PERCENT for link in links]
                    rounds.append(WeakestLinkRound(allotted_time, links))
            rounds[round_num - 1].add_question(question, answer)

for i in range(len(rounds)) :
    round = rounds[i]
    print('Loaded', len(round.questions), 'questions for round', i+1)
print('Loaded', len(final_round.questions), 'questions for the final round')
print()

expected_players = len(rounds) + 2
if expected_players > len(players) :
    print('There are more rounds than players!')
elif expected_players < len(players) :
    print('There are more players than rounds!')
else :
    print('There are the perfect amount of players!')
print()

game = WeakestLinkGame(players, rounds, final_round)
print('Ready to start game!')
print()
print('Your choices during the round are Z=ztupid (wrong), X=bank, C=correct\n')

game.run()