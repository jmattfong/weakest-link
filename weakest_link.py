#!/usr/bin/env python3

import csv
import sys
import time
import threading
import socketserver
import http.server
import re
import json

from util import dollars, format_time, debug
from questions import Questions
from final_round import FinalRound
from round import WeakestLinkRound
from game import WeakestLinkGame

PORT=8080

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
    (170, ROUND_1_LINKS),
    (160, ROUND_2_LINKS),
    (150, ROUND_3_LINKS),
    (140, ROUND_4_LINKS),
    (130, ROUND_5_LINKS),
    (120, ROUND_6_LINKS)
]

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
            response = get_current_round_details()
            self.wfile.write(bytes(json.dumps(response), 'utf-8'))
        elif None != re.search('/api/final-round', self.path):
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(b"Final")
        else:
            # serve files, and directory listings by following self.path from ./html/ directory
            http.server.SimpleHTTPRequestHandler.do_GET(self)

def start_server():
    httpd = socketserver.ThreadingTCPServer(('', PORT), CustomHandler)
    httpd.serve_forever()

def get_current_round_details() :
    return {
        "players": game.players,
        "currentBank": dollars(game.get_current_round().round_bank, color=False),
        "totalBank": dollars(game.total_bank, color=False),
        "bankLinks": [dollars(link, color=False) for link in game.get_current_round().bank_links],
        "currentLink": game.get_current_round().current_link,
        "currentPlayer": game.get_current_round().get_current_player_num(),
        "time": format_time(game.get_current_round().seconds_remaining)
    }

def get_final_round_details() :
    return {
    }

"""
Main method. Why are python servers so anti OOP??
"""

# Parse the arguments
if len(sys.argv) < 5 :
    print('Not enough players provided! Usage: ./weakest_link.py <path-to-questions.csv> Player1 Player2 ... PlayerN')
    sys.exit(1)
question_file = sys.argv[1]
players = sys.argv[2:]
debug('Welcome players', ', '.join(players))

# Read the questions from the file
questions = Questions()
with open(question_file) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader :
        round_num = int(row[0])
        question = row[1]
        answer = row[2]
        questions.add_question(question, answer)

# Setup the rounds
rounds = []
expected_rounds = len(players) - 2
planned_rounds = len(ROUNDS)

# Create the normal amound of rounds
for (allotted_time, links) in ROUNDS :
    debug('Adding Round with allotted time', allotted_time)
    links = [link * DOLLAR_PERCENT for link in links]
    rounds.append(WeakestLinkRound(allotted_time, links, questions))

# Add extra rounds to match the number of players, if needed
for i in range(planned_rounds, expected_rounds) :
    debug('Adding extra round')
    (allotted_time, links) = ROUNDS[-1]
    links = [link * DOLLAR_PERCENT for link in links]
    rounds.append(WeakestLinkRound(allotted_time, links, questions))

final_round = FinalRound(questions)
game = WeakestLinkGame(players, rounds, final_round)

# Start the server
t = threading.Thread(target=start_server)
debug("Starting server at port", PORT)
print('Player view: http://localhost:' + str(PORT) + '/index.html')
print()
t.start()

# Start the game!
print('Ready to start game!\n')
print('Your choices during the round are Z=ztupid (wrong), X=bank, C=correct\n')
game.run()
