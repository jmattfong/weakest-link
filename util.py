from datetime import timedelta
import random

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

def starts_with_vowel(word) :
    return word[0].lower() in ['a', 'e', 'i', 'o', 'u']

def green(message) :
    return GREEN + BOLD + str(message) + END + END

def random_mean_word() :
    return random.choice([
        'paltry',
        'meager',
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
