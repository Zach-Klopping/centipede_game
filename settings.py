from os import environ

DEBUG = False

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

SESSION_CONFIGS = [
    dict(
        name='centipede',
        display_name="Centipede Game",
        num_demo_participants=2,
        app_sequence=['centipede_game_1', 'centipede_game_2', 'centipede_game_3', 'centipede_game_4'],
    ),
]

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False

ROOMS = [
    dict(name='full_experiment', 
         display_name='Full Experiment Room',),
]

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = 'ze+i3u9b5cjw&q$puki3i6k)=5_^lzs0-0o=auta3w_(ei1#%4'

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree']

STATICFILES_STORAGE = ''
