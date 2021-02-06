import random

USER_NAMES = [
    'Raul Horowitz',
    'Amelia Canipe',
    'Lurlene Harting',
    'Grant Headen',
    'Kenna Mera',
    'Shanae Marciano',
    'Allegra Credle',
    'Dalila Glazier',
    'Terisa Davisson',
    'Clifton Lofton',
    'Evalyn Stpeter',
    'Chaya Matter',
    'Windy Macmillan',
    'Setsuko Cogan',
    'Merilyn Bigby',
    'Fausto Meza',
    'Olin Cullens',
    'Marlyn Whittemore',
    'Patience Goings',
    'Kiley Nees',
    'Tonia Withey',
    'Jaymie Steffen',
    'Maira Lyden',
    'Piper Birk',
    'Vesta Gautreaux',
    'Ty Ferretti',
    'Kristin Blanding',
    'Nubia Cella',
    'Yolando Wareham',
    'Lane Rexroat',
    'Alden Ackerman',
    'Rebekah Casali',
    'Nanci Rakowski',
    'Grover Scioneaux',
    'Sharika Sharon',
    'Shelba Wattles',
    'Easter Cardinal',
    'Alana Bourgeois',
    'Tyree Pompey',
    'Cory Craghead',
    'Bonita Midgett'
]


RANDOM_GENERATOR_DATA = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890'


def get_random_name():
    idx = random.randint(0,40)
    return USER_NAMES[idx]


def get_random_user_id():
    random_id = ''
    for i in range(0, 32):
        idx = random.randint(0,62)
        random_id += RANDOM_GENERATOR_DATA[idx]
    return random_id
