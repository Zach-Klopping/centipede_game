from otree.api import *
import numpy as np


doc = """ oTree App for the Centipede Game 4 """


class Constants(BaseConstants):
    name_in_url = 'centipede_game_4'
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
        if player.id_in_group == 2 and player.round_number % 2 != 0 and player.group.game_on:
            return True
        elif player.id_in_group == 1 and player.round_number % 2 == 0 and player.group.game_on:
            return True
        else:
            return False

    def vars_for_template(player):
        return dict(
            game = 4,
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
            game=4,
            last_node=player.group.last_node,
            large_pile=Constants.large_piles[player.group.last_node-1],
            small_pile=Constants.small_piles[player.group.last_node-1],
            large_pile_pass=Constants.large_piles[-1],
            small_pile_pass=Constants.small_piles[-1]
        )
    
    def before_next_page(player, timeout_happened):
        # Determine the game number
        game_number = 4  # or whatever variable you track for this game

        # Flip player_id for games 2 and 4
        if game_number in [2, 4]:
            player_id_flipped = 3 - player.id_in_group  # swaps 1<->2
        else:
            player_id_flipped = player.id_in_group

        # store this round's data in participant.vars
        round_data = {
            'game_number': 4,
            'round_number': player.round_number,
            'player_id': player_id_flipped,
            'take': player.field_maybe_none('take'),
            'payoff': player.payoff_final
        }
        
        if 'game_data' not in player.participant.vars:
            player.participant.vars['game_data'] = []
        
        player.participant.vars['game_data'].append(round_data)
        print(player.participant.vars['game_data'])


class Conclusion(Page):
    def is_displayed(player):
        return not player.group.game_on

    def vars_for_template(player):
        game_data = player.participant.vars.get('game_data', [])
        
        for row in game_data:
            # Your own payoff as float
            my_payoff = float(row.get('payoff', 0) or 0)
            
            # Opponent payoff logic
            if row.get('take'):
                opponent_payoff = my_payoff / 3  # you took, opponent gets 1/3
            else:
                opponent_payoff = my_payoff * 3  # you passed, opponent gets 3x
            
            # Store formatted strings for display
            row['payoff_str'] = f"${my_payoff:.2f}"
            row['opponent_payoff_str'] = f"${opponent_payoff:.2f}"
            
            # Also store numeric values if needed
            row['opponent_payoff'] = opponent_payoff

        # Total payoff calculation
        total_payoff = sum(float(d.get('payoff', 0) or 0) for d in game_data)
        total_payoff_str = f"${total_payoff:.2f}"
        
        return dict(
            game_data=game_data,
            total_payoff=total_payoff_str,
            player_name = player.participant.vars['identification'],
        )
    

page_sequence = [WaitPage1, Decision, WaitPage2, Results, Conclusion]