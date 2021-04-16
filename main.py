#!/usr/bin/env python3

import csv
import sys
import time
import threading
import socketserver
import http.server
import re
import json

from weakest_link.util import dollars, format_time, debug
from weakest_link.questions import Questions
from weakest_link.final_round import FinalRound
from weakest_link.round import WeakestLinkRound
from weakest_link.game import WeakestLinkGame

# Constants

PORT=1990

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
    (160, ROUND_1_LINKS),
    (150, ROUND_2_LINKS),
    (140, ROUND_3_LINKS),
    (130, ROUND_4_LINKS),
    (120, ROUND_5_LINKS),
    (110, ROUND_6_LINKS)
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
        else:
            # serve files, and directory listings by following self.path from ./html/ directory
            http.server.SimpleHTTPRequestHandler.do_GET(self)

def start_server():
    httpd = socketserver.ThreadingTCPServer(('', PORT), CustomHandler)
    httpd.serve_forever()

def get_current_round_details() :
    response = {
            "round": game.get_current_round_name(),
            "players": game.get_players(),
            "currentBank": game.get_current_bank(color=False),
            "totalBank": game.get_total_bank(color=False),
            "bankLinks": game.get_bank_links(),
            "currentLink": game.get_current_link(),
            "currentPlayer": game.get_current_player_num(),
            "time": game.get_time_remaining()
        }
    if game.get_current_round_name() == 'Final':
        response["scores"] = final_round.get_scores()
    return response

"""
Main method. Kinda.
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
        question = row[0]
        answer = row[1]
        questions.add_question(question, answer)

# Setup the rounds
rounds = []
expected_rounds = len(players) - 2
planned_rounds = len(ROUNDS)

# Create the normal amound of rounds
offset = 0 if planned_rounds <= expected_rounds else planned_rounds - expected_rounds
for i in range(0, min(expected_rounds, len(ROUNDS))) :
    (allotted_time, links) = ROUNDS[i + offset]
    debug('Adding Round with allotted time', allotted_time)
    links = [link * DOLLAR_PERCENT for link in links]
    rounds.append(WeakestLinkRound(str(i), allotted_time, links, questions))

# Add extra rounds to match the number of players, if needed
for i in range(planned_rounds, expected_rounds) :
    debug('Adding extra round')
    (allotted_time, links) = ROUNDS[-1]
    links = [link * DOLLAR_PERCENT for link in links]
    rounds.append(WeakestLinkRound(str(i+1), allotted_time - 10, links, questions))

final_round = FinalRound(players, questions)
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
