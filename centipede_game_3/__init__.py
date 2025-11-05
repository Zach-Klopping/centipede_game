from otree.api import *
import numpy as np

import os

doc = """ oTree App for the Centipede Game 1 """


class Constants(BaseConstants):
    domain = 'http://localhost:8000'
    name_in_url = '3'
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

        # Matrix of moves and payoffs
        # --------------------------------------------------------------------------------
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

    def creating_session(self):
        if self.round_number == 1:
            self.group_randomly(fixed_id_in_group=True)
            print(f"GROUPING ROUND {self.round_number}")
        else:
            # Explicitly copy from round 1
            self.group_like_round(1)
            print(f"SKIP GROUPING ROUND {self.round_number}")

        current_round = self.round_number
        # print(f'>> creating_session called for round {current_round}')

        self.game = int(np.ceil(current_round / Constants.num_nodes))
        self.game_node = int(current_round - (np.ceil(current_round / Constants.num_nodes) - 1) * Constants.num_nodes)

        # for g in self.get_groups():
        #     ids = [p.participant.id_in_session for p in g.get_players()]
        #     print(f'Round {self.round_number} group (by ID): {ids}')



class Group(BaseGroup):

    game_on = models.BooleanField(initial=True)
    game_outcome = models.IntegerField(initial=0)
    last_node = models.IntegerField(initial=1)

    def stop_game(self):
        players = self.get_players()
        someone_took = False
        results_dir = 'results'
        os.makedirs(results_dir, exist_ok=True)  # ✅ ensure 'results/' exists

        for p in players:
            value = p.field_maybe_none('take')
            print(f'Stop Game: {value} ({type(value)})')

            if value is True:
                self.game_on = False
                self.game_outcome = p.id_in_group
                self.last_node = self.round_number
                print(f'Game stopped by Player {p.id_in_group} at node {self.last_node}')

                rows = []

                for p in self.get_players():
                    if p.field_maybe_none('take') == True:
                        payoff = Constants.large_piles[p.group.last_node - 1]
                        p.payoff = payoff
                    else:
                        payoff = Constants.small_piles[p.group.last_node - 1]
                        p.payoff = payoff

                        # Build one row for this player
                    row = {
                        'game_id': self.session.code + "-" + Constants.name_in_url  + "-" + str(self.id_in_subsession),
                        'game':Constants.name_in_url,
                        'participant_code': p.participant.code,
                        'participant_id': p.id_in_group,
                        'player_name': p.participant.label,
                        'round_number': p.round_number,
                        'current_node': p.subsession.round_number,
                        'take': p.field_maybe_none('take'),
                        'group_color': '',
                        'payoff': payoff
                    }
                    
                    rows.append(row)

                new_df = pd.DataFrame(rows)
                filename = 'centipede_results.csv'
                file_path = os.path.join(results_dir, filename)

                print(f'Output Payoff to a file: {file_path}')
                if os.path.exists(file_path):
                    # ✅ Load existing file
                    existing_df = pd.read_csv(file_path)
                    # ✅ Append new rows
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                else:
                    combined_df = new_df
                combined_df.to_csv(file_path, index=False)

                generate_result_html()
                generate_full_centipede_report()
                return

class Player(BasePlayer):
    current_node = models.IntegerField(initial=1)
    current_game = models.IntegerField(initial=1)
    player_name = models.StringField(label="What is your name?")
    player_take = models.StringField()
    opponent_label = models.StringField()
    current_app_name = models.StringField()


    take = models.BooleanField(
        label='',
        widget=widgets.RadioSelectHorizontal,
    )

from otree.api import Currency as c, currency_range
from sqlalchemy import false

from ._builtin import Page, WaitPage
from .models import Constants
import pandas as pd
from results.load_results import generate_result_html
from results.load_results import generate_full_centipede_report

class FirstPage(Page):
    def is_displayed(self):
        #print(f'FirstPage - is_displyed')
        return self.round_number == 1


class Welcome(FirstPage):

    def is_displayed(self):
        # Show only if this is the first node
        return self.round_number == 1


class Instructions(FirstPage):

    def vars_for_template(self):
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

    def before_next_page(self):
        self.player.current_app_name = Constants.name_in_url
        self.player.player_name = self.player.participant.label
        self.player.player_take = "False"

class Practice1Page1(FirstPage):
    pass


class Practice1Page2(FirstPage):
    def vars_for_template(self):
        return dict(
            large_pile_practice=Constants.large_piles,
            small_pile_practice=Constants.small_piles,
            large_pile_practice_second=Constants.large_piles[1],
            small_pile_practice_second=Constants.small_piles[1],
        )


class Practice1Page3(FirstPage):

    def vars_for_template(self):
        return dict(
            large_pile_practice=Constants.large_piles,
            small_pile_practice=Constants.small_piles,
            large_pile_practice_second=Constants.large_piles[1],
            small_pile_practice_second=Constants.small_piles[1],
        )


class Practice1Page4(FirstPage):

    def vars_for_template(self):
        return dict(
            large_pile_practice=Constants.large_piles,
            small_pile_practice=Constants.small_piles,
            large_pile_practice_second=Constants.large_piles[1],
            small_pile_practice_second=Constants.small_piles[1],
        )


class Practice2Page1(FirstPage):

    def vars_for_template(self):
        return dict(
            large_pile_practice_second=Constants.large_piles[1],
            small_pile_practice_second=Constants.small_piles[1],
            large_pile_practice_third=Constants.large_piles[2],
            small_pile_practice_third=Constants.small_piles[2]
        )


class Practice2Page2(FirstPage):

    def vars_for_template(self):
        return dict(
            large_pile_practice_last=Constants.large_piles[-2],
            small_pile_practice_last=Constants.small_piles[-2],
            large_pile_practice_pass=Constants.large_piles[-1],
            small_pile_practice_pass=Constants.small_piles[-1],
        )


class Practice2Page3(FirstPage):
    pass


class WaitPage1(WaitPage):

    def is_displayed(self):
        #print(f'WaitPage1 - is_displyed')
        return self.round_number == 1

    wait_for_all_groups = False


class Decision(Page):

    form_model = 'player'
    form_fields = ['take']

    def is_displayed(self):
        # print(
        #     f'Decision - is_displayed | '
        #     f'Player ID in Group: {self.player.id_in_group} | '
        #     f'Round Number: {self.round_number} | '
        #     f'game_on: {self.group.game_on}'
        # )
        if self.player.id_in_group == 1 and self.round_number % 2 != 0 and self.group.game_on:
            return True
        elif self.player.id_in_group == 2 and self.round_number % 2 == 0 and self.group.game_on:
            return True
        else:
            return False

    def vars_for_template(self):
        #print(f'Decision - vars_for_template:  Player {self.player.id_in_group} advance: {self.subsession.game_node}')
        self.player.current_app_name = Constants.name_in_url
        name = self.player.participant.label
        result_html_contents = generate_result_html(name)

        return dict(
            result_html_contents=result_html_contents,
            player_name=name,
            game =  self.player.current_app_name,
            num_nodes =  Constants.num_nodes,
            game_node = self.subsession.game_node,
            large_pile = Constants.large_piles[self.subsession.game_node - 1],
            small_pile = Constants.small_piles[self.subsession.game_node - 1]
        )

    def before_next_page(self):
        print(f'Decision - before_next_page:  Player {self.player.id_in_group} submitted take: {self.player.take}')
        opponent = self.player.get_others_in_group()[0]
        self.player.current_app_name = Constants.name_in_url
        self.player.player_name = self.player.participant.label
        self.player.player_take = "False"
        self.player.opponent_label = opponent.participant.label

        if self.player.take:
            # Player takes: stop the game
            self.player.player_take = "True"
            self.player.current_game += 1
            self.player.current_node = (self.player.current_game - 1) * Constants.num_nodes + 1
            print(f'Decision - before_next_page:  next_current_game {self.player.current_game } next_current_node: {self.player.current_node }')
            self.player.group.game_on = False
            self.group.stop_game()


class WaitPage2(WaitPage):

    wait_for_all_groups = False  # default is fine
    def is_displayed(self):
        visible = self.group.game_on
        print(f'WaitPage2 | Round {self.round_number} | is_displayed: {visible}')
        return visible

    def after_all_players_arrive(self):
        print(f'WaitPage2 - after_all_players_arrive | game_on: {self.group.game_on}')
        # Example: increment node number if needed
        # if self.group.game_on:
        #      self.subsession.game_node += 1
        #      print(f'WaitPage2 - after_all_players_arrive | Next node: {self.subsession.game_node}')
        group = self.group
        subsession = self.subsession

        players = group.get_players()
        someone_took = any(p.field_maybe_none('take') for p in players)

        if someone_took:
            print('Someone took — stopping game.')
            #group.stop_game()
        else:
            print(f'WaitPage2 - Node advanced to: {subsession.game_node}')

            if subsession.game_node == Constants.num_nodes:
                # Reached end, no one took
                print(f'Everyone passed on the last node → stopping game.')
                group.stop_game()
            else:
                print(f'Everyone passed → keep going to next round.')



class Results(Page):
    def is_displayed(self):
        visible = not self.group.game_on
        print(f'Results | round: {self.round_number} | game: {self.subsession.game} | visible: {visible}')
        return visible  # Show Results ONLY when the game has stopped

    def before_next_page(self):
        print(f'Results - before_next_page - {self.player.payoff}')
        opponent = self.player.get_others_in_group()[0]
        participant = self.player.participant
        self.player.opponent_label = opponent.participant.label
        participant.vars['total_payoff'] = participant.vars.get('total_payoff', 0) + self.player.payoff

    def vars_for_template(self):
        name = self.player.participant.label
        participant_code = self.player.participant.code
        result_html_contents = generate_result_html(name, False)

        return dict(
            result_html_contents=result_html_contents,
            next_link = None,
            player_name = name,
            game=Constants.name_in_url,
            Constants=Constants,
            last_node=self.group.last_node,
            large_pile=Constants.large_piles[self.group.last_node-1],
            small_pile=Constants.small_piles[self.group.last_node-1],
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
    def is_displayed(self):
        print(f'WaitPage3 - is_displyed')
        return self.group.game_on and self.round_number in Constants.last_rounds

    wait_for_all_groups = True
    after_all_players_arrive = 'advance_game'



page_sequence = [
    WaitPage1,
    Decision,
    WaitPage2,
    Results,
    WaitPage3
                ]
