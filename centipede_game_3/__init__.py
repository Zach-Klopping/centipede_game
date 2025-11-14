from otree.api import *
import numpy as np


doc = """ oTree App for the Centipede Game 3 """


class Constants(BaseConstants):
    name_in_url = 'centipede_game_3'
    players_per_group = 2
    num_nodes = 6
    num_games = 1
    num_rounds = num_nodes * num_games

    first_rounds = np.arange(1, num_rounds, num_nodes)
    last_rounds = np.arange(num_nodes,num_rounds + 1, num_nodes)

    large_pile = 30
    small_pile = 10
    base = 2

    large_piles = []
    small_piles = []

    for node in range(num_nodes + 1):
        large_piles.append(large_pile * base ** node)
        small_piles.append(small_pile * base ** node)


class Subsession(BaseSubsession):
    pass
        

class Group(BaseGroup):
    game_on = models.BooleanField(initial=True)
    game_outcome = models.IntegerField(initial=0)
    last_node = models.IntegerField(initial=1)

    def stop_game(group):
        players = group.get_players()
        for p in players:
            value = p.field_maybe_none('take')
            if value is True:
                group.game_on = False
                group.game_outcome = p.id_in_group
                group.last_node = p.round_number
            
                # assign payoffs
                for q in players:
                    if q.id_in_group == p.id_in_group:  # the player who took
                        q.payoff_final = Constants.large_piles[group.last_node - 1]
                    else:  # the other player
                        q.payoff_final = Constants.small_piles[group.last_node - 1]
                break


class Player(BasePlayer):
    first = models.BooleanField(initial=False)
    player_take = models.StringField()
    take = models.BooleanField(label='', widget=widgets.RadioSelectHorizontal)
    payoff_final = models.CurrencyField()


class WaitPage1(WaitPage):
    def is_displayed(player):
        return player.round_number == 1
    wait_for_all_groups = False


class Decision(Page):
    form_model = 'player'
    form_fields = ['take']

    def is_displayed(player):
        if player.id_in_group == 1 and player.round_number % 2 != 0 and player.group.game_on:
            return True
        elif player.id_in_group == 2 and player.round_number % 2 == 0 and player.group.game_on:
            return True
        else:
            return False

    def vars_for_template(player):
        return dict(
            game = 3,
            num_nodes =  Constants.num_nodes,
            game_node = player.round_number,
            large_pile = Constants.large_piles[player.round_number - 1],
            small_pile = Constants.small_piles[player.round_number - 1]
        )

    def before_next_page(player, timeout_happened):
        group = player.group

        if player.id_in_group == 1:
            player.first = True

        if player.take:
            player.player_take = "True"
            player.group.game_on = False
            group.stop_game()
        else:
            player.player_take = "False"
            if player.round_number < Constants.num_nodes:
                pass
            else:
                group.stop_game()


class WaitPage2(WaitPage):
    wait_for_all_groups = False
    def is_displayed(player):
        visible = player.group.game_on
        return visible

    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        someone_took = any(p.field_maybe_none('take') for p in players)

        if someone_took:
            pass
        else:
            if group.round_number == Constants.num_nodes:
                group.stop_game()
            else:
                pass
                

class Results(Page):
    def is_displayed(player):
        visible = not player.group.game_on
        return visible

    def before_next_page(player, timeout_happened):
        participant = player.participant
        participant.vars['total_payoff'] = participant.vars.get('total_payoff', 0) + player.payoff

    def vars_for_template(player):
        return dict(
            next_link = None,
            player_name = player.participant.vars['identification'],
            game=3,
            last_node=player.group.last_node,
            large_pile=Constants.large_piles[player.group.last_node-1],
            small_pile=Constants.small_piles[player.group.last_node-1],
            large_pile_pass=Constants.large_piles[-1],
            small_pile_pass=Constants.small_piles[-1]
        )
    
    def before_next_page(player, timeout_happened):
        # store this round's data in participant.vars
        round_data = {
            'game_number': 3,
            'round_number': player.round_number,
            'player_id': player.id_in_group,
            'take': player.field_maybe_none('take'),
            'payoff': player.payoff_final
        }
        
        if 'game_data' not in player.participant.vars:
            player.participant.vars['game_data'] = []
        
        player.participant.vars['game_data'].append(round_data)

    def app_after_this_page(player, upcoming_apps):
        if not player.group.game_on:
            return upcoming_apps[0]
        return None


class WaitPage3(WaitPage):
    def is_displayed(player):
        return player.group.game_on and player.round_number in Constants.last_rounds

    wait_for_all_groups = True


page_sequence = [WaitPage1, Decision, WaitPage2, Results, WaitPage3]