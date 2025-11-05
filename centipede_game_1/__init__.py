from otree.api import *
import numpy as np


doc = """ oTree App for the Centipede Game 1 """


class Constants(BaseConstants):
    name_in_url = 'centipede_game_1'
    players_per_group = 2
    num_nodes = 6
    num_games = 1
    num_rounds = num_nodes * num_games

    first_rounds = np.arange(1,num_rounds,num_nodes)
    last_rounds = np.arange(num_nodes,num_rounds+1,num_nodes)

    large_pile = 30
    small_pile = 10
    base = 2

    large_piles = []
    small_piles = []

    for node in range(num_nodes + 1):
        large_piles.append(large_pile * base ** node)
        small_piles.append(small_pile * base ** node)

        # Vars for Instructions/Practice
        large_piles_practice = large_piles.copy()
        small_piles_practice = small_piles.copy()

        columns_range = range(4 + num_nodes)
        rounds_range = range(1, num_nodes + 1)

        # Merge the two Piles alternating elements
        payoff_red_practice = large_piles_practice.copy()
        for i in range(len(large_piles_practice)):
            if i % 2 != 0:
                payoff_red_practice[i] = small_piles_practice[i]

        # Merge the two Piles alternating elements
        payoff_blue_practice = small_piles_practice.copy()
        for i in range(len(payoff_blue_practice)):
            if i % 2 != 0:
                payoff_blue_practice[i] = large_piles_practice[i]

        # Table of moves for each game node
        movesList = ['P' for n in range(num_nodes)]
        movesMatrix = [movesList.copy()]

        for i in range(num_nodes):
            mc = movesList.copy()
            for j in range(num_nodes):
                if j <= i:
                    mc[i - j] = ''
                    mc[i] = 'T'
            mc.reverse()
            movesMatrix.append(mc)

        movesMatrix.reverse()

        # Zip variables needed for Instructions
        instructionsMatrix = list(zip(movesMatrix, large_piles_practice, small_piles_practice,
                                      payoff_red_practice, payoff_blue_practice))

class Subsession(BaseSubsession):
    game = models.IntegerField(initial=1)
    game_node = models.IntegerField(initial=1)

    def creating_session(player):
        if player.round_number == 1:
            player.group_randomly(fixed_id_in_group=True)
            print(f"GROUPING ROUND {player.round_number}")
        else:
            # Explicitly copy from round 1
            player.group_like_round(1)
            print(f"SKIP GROUPING ROUND {player.round_number}")

        current_round = player.round_number

        player.game = int(np.ceil(current_round / Constants.num_nodes))
        player.game_node = int(current_round - (np.ceil(current_round / Constants.num_nodes) - 1) * Constants.num_nodes)


class Group(BaseGroup):
    game_on = models.BooleanField(initial=True)
    game_outcome = models.IntegerField(initial=0)
    last_node = models.IntegerField(initial=1)

    def stop_game(player):
        players = player.get_players()
        for p in players:
            value = p.field_maybe_none('take')
            print(f'Stop Game: {value} ({type(value)})')

            if value is True:
                player.game_on = False
                player.game_outcome = p.id_in_group
                player.last_node = player.round_number
                print(f'Game stopped by Player {p.id_in_group} at node {player.last_node}')


class Player(BasePlayer):
    current_node = models.IntegerField(initial=1)
    current_game = models.IntegerField(initial=1)
    player_name = models.StringField(label="What is your name?")
    player_take = models.StringField()
    opponent_label = models.StringField()
    current_app_name = models.StringField()
    take = models.BooleanField(label='', widget=widgets.RadioSelectHorizontal)


class FirstPage(Page):
    def is_displayed(player):
        return player.round_number == 1


class Welcome(FirstPage):
    def is_displayed(player):
        return player.round_number == 1


class Instructions(FirstPage):
    def vars_for_template(player):
        return dict(
            turns=int(Constants.num_rounds / 2),
            instructionsMatrix=Constants.instructionsMatrix,
            rounds_range=Constants.rounds_range,
            large_pile_practice=Constants.large_piles,
            small_pile_practice=Constants.small_piles,
            large_pile_practice_second=Constants.large_piles[1],
            small_pile_practice_second=Constants.small_piles[1],
            large_pile_practice_third=Constants.large_piles[2],
            small_pile_practice_third=Constants.small_piles[2],
            large_pile_practice_last=Constants.large_piles[-2],
            small_pile_practice_last=Constants.small_piles[-2],
            large_pile_practice_pass=Constants.large_piles[-1],
            small_pile_practice_pass=Constants.small_piles[-1]
        )

    def before_next_page(player):
        player.player.current_app_name = Constants.name_in_url
        player.player.player_name = player.player.participant.label
        player.player.player_take = "False"


class WaitPage1(WaitPage):
    def is_displayed(player):
        return player.round_number == 1

    wait_for_all_groups = False


class Decision(Page):
    form_model = 'player'
    form_fields = ['take']

    def is_displayed(player):
        if player.player.id_in_group == 1 and player.round_number % 2 != 0 and player.group.game_on:
            return True
        elif player.player.id_in_group == 2 and player.round_number % 2 == 0 and player.group.game_on:
            return True
        else:
            return False

    def vars_for_template(player):
        return dict(
            game = player.player.current_app_name,
            num_nodes =  Constants.num_nodes,
            game_node = player.subsession.game_node,
            large_pile = Constants.large_piles[player.subsession.game_node - 1],
            small_pile = Constants.small_piles[player.subsession.game_node - 1]
        )

    def before_next_page(player):
        opponent = player.player.get_others_in_group()[0]
        player.player.current_app_name = Constants.name_in_url
        player.player.player_name = player.player.participant.label
        player.player.player_take = "False"
        player.player.opponent_label = opponent.participant.label

        if player.player.take:
            # Player takes: stop the game
            player.player.player_take = "True"
            player.player.current_game += 1
            player.player.current_node = (player.player.current_game - 1) * Constants.num_nodes + 1
            player.player.group.game_on = False
            player.group.stop_game()


class WaitPage2(WaitPage):
    wait_for_all_groups = False  # default is fine
    def is_displayed(player):
        visible = player.group.game_on
        print(f'WaitPage2 | Round {player.round_number} | is_displayed: {visible}')
        return visible

    def after_all_players_arrive(player):
        group = player.group
        subsession = player.subsession

        players = group.get_players()
        someone_took = any(p.field_maybe_none('take') for p in players)

        if someone_took:
            pass
        else:
            if subsession.game_node == Constants.num_nodes:
                group.stop_game()
            else:
                pass
                

class Results(Page):
    def is_displayed(player):
        visible = not player.group.game_on
        return visible  # Show Results ONLY when the game has stopped

    def before_next_page(player):
        opponent = player.player.get_others_in_group()[0]
        participant = player.player.participant
        player.player.opponent_label = opponent.participant.label
        participant.vars['total_payoff'] = participant.vars.get('total_payoff', 0) + player.player.payoff

    def vars_for_template(player):
        return dict(
            next_link = None,
            game=player.player.current_app_name,
            Constants=Constants,
            last_node=player.group.last_node,
            large_pile=Constants.large_piles[player.group.last_node-1],
            small_pile=Constants.small_piles[player.group.last_node-1],
            large_pile_pass=Constants.large_piles[-1],
            small_pile_pass=Constants.small_piles[-1]
        )

    def app_after_this_page(player, upcoming_apps):
        print(f'Results - App After This Page: {player.group.game_on}')
        if not player.group.game_on:
            # Jump to final round of this app
            print(f'Results - App After This Page - Run next game!')
            return upcoming_apps[0]  # jumps to next app in app_sequence
        return None  # proceed normally


class WaitPage3(WaitPage):
    def is_displayed(player):
        return player.group.game_on and player.round_number in Constants.last_rounds

    wait_for_all_groups = True
    after_all_players_arrive = 'advance_game'


page_sequence = [Welcome, Instructions, WaitPage1, Decision, WaitPage2, Results, WaitPage3]