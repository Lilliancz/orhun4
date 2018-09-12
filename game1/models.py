from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import inflect
import random
from django.conf import settings
from otree.models_concrete import PageCompletion

author = 'Lillian Chen. Special thanks to Eli Pandolfo for the basic structure, and Xiaotian Lu for initial edits.'

''' notes

'''


class Constants(BaseConstants):

    # can be changed to anything
    name_in_url = 'Game1'

    # Do not change
    players_per_group = 3
    num_rounds = 1


class Subsession(BaseSubsession):
    # everything in this class is only run once

    def creating_session(self):

        #for p in self.get_players():
            # assign firm switching chance to 1 for 10 percent of the people
            # change the value after >= to set percentage
            #p.participant.vars['firm_switch'] = (1 if random.random() >= 0.85 else 0)

        if self.round_number == 1:
            for p in self.get_players():
                p.participant.vars['random_number'] = random.randint(1, 10)

                # these are variable and can be set to anything by the person running the experiment.
                # 0 and 100 are the default values
                lower_bound = self.session.config.get('lower_bound')
                upper_bound = self.session.config.get('upper_bound')

                problems = []
                answers = []

                # create list of problems.
                # this is done serverside instead of clientside because everyone has the same problems, and
                # because converting numbers to words is easier in python than in JS.

                # JSON converts python tuples to JS lists, so this data structure is a list
                # of pairs, each holding a triple and its sum.
                # [ ( ('two', 'fifteen', 'forty four'), 61 )... ]

                # numbers are randomly generated between lower_bound and upper_bound, both inclusive.
                # inflect is used to convert numbers to words easily
                n2w = inflect.engine()

                # assuming no one can do more than 500 problems in 2 minutes
                # or 200
                for n in range(200):
                    v1 = random.randint(lower_bound, upper_bound)
                    v2 = random.randint(lower_bound, upper_bound)
                    v3 = random.randint(lower_bound, upper_bound)

                    answer = v1 + v2 + v3

                    s1 = n2w.number_to_words(v1).capitalize()
                    s2 = n2w.number_to_words(v2)
                    s3 = n2w.number_to_words(v3)

                    words = (s1, s2, s3)
                    entry = (words, answer)

                    problems.append(entry)
                    answers.append(answer)

                p.participant.vars['game1_problems'] = problems
                p.participant.vars['game1_answers'] = answers


class Group(BaseGroup):
    # set payoffs when all players arrive, so that it only fires once for randomization to work correctly

    def set_condition(self):
        for player in self.get_players():
            condition = player.group_id % 4
            print("condition is " + str(condition))
            if condition <= 1:
                player.condition = "chooser"
                player.firm = ""
            if condition == 2:
                player.condition = "randomA"
                player.firm = "A"
            if condition == 3:
                player.condition = "randomB"
                player.firm = "B"

    def set_payoffs(self):
        # in case 2 players have a tied score, chance decides how bonuses are distributed
        p1 = self.get_player_by_id(1)
        p2 = self.get_player_by_id(2)
        p3 = self.get_player_by_id(3)

        # sorted() is guaranteed to be stable, so the list is shuffled first to ensure randomness
        players = sorted(random.sample([p1, p2, p3], k=3), key=lambda x: x.game1_score, reverse=True)

        for i in range(3):
            # if score is zero, auto rank 3rd, no bonus
            if players[i].game1_score == 0:
                players[i].game1_rank = 3
                players[i].participant.vars['game1_rank'] = 3
                players[i].game1_bonus = 0
                players[i].participant.vars['game1_bonus'] = 0
            # if not score of zero, then rank in order of highest score in game 1
            else:
                players[i].game1_rank = i + 1
                players[i].participant.vars['game1_rank'] = i + 1
                # need to change bonus structure here
                if players[i].game1_rank == 1:
                    players[i].game1_bonus = self.session.config.get('first_place_bonus')
                    players[i].participant.vars['game1_bonus'] = self.session.config.get('first_place_bonus')
                    print("1st place is " + str(players[i].id))
                if players[i].game1_rank == 2:
                    players[i].game1_bonus = self.session.config.get('second_place_bonus')
                    players[i].participant.vars['game1_bonus'] = self.session.config.get('second_place_bonus')
                    print("2nd place is " + str(players[i].id))
                if players[i].game1_rank == 3:
                    players[i].game1_bonus = 0
                    players[i].participant.vars['game1_bonus'] = 0
                    print("3nd place is " + str(players[i].id))
            # sets the participant.vars to transfer to next round
            players[i].participant.vars['game1_attempted'] = players[i].attempted
            players[i].participant.vars['game1_score'] = players[i].game1_score
            players[i].baseline_bonus = players[i].participant.vars['baseline_bonus']
            players[i].total_bonus = players[i].baseline_bonus + players[i].game1_bonus
            players[i].participant.vars['total_bonus'] = players[i].total_bonus


class Player(BasePlayer):

    # whether they will switch 1 or not 0
    #firm_switch = models.IntegerField()

    # number of correct answers in game1 task
    game1_score = models.IntegerField()

    # problems from game1 task
    game1_answers = models.StringField()

    # player's rank out of 3
    game1_rank = models.IntegerField()

    # player's bonus for game 1
    game1_bonus = models.CurrencyField()

    # player's bonus for baseline
    baseline_bonus = models.CurrencyField()

    # combined bonus for game 1 and baseline
    total_bonus = models.CurrencyField()

    # number of problems attempted
    attempted = models.IntegerField()

    condition = models.StringField()

    # firm chosen
    firm = models.StringField(
        # choices=['A', 'B'],
        # widget=widgets.RadioSelect
    )

    # whether skipped to end
    skip_to_end = models.BooleanField(initial=True)
    
    # arrival times
    time_ChooseFirm = models.StringField()
    time_Game1Firm = models.StringField()
    time_Game1 = models.StringField()
    time_Results1 = models.StringField()
    time_Debrief = models.StringField()
    time_FinalSurvey = models.StringField()
    time_PerformancePayment = models.StringField()
    # time_Survey2 = models.StringField()
    # time_Survey45 = models.StringField()

    # timeout happened
    TimeoutWhatHappens = models.BooleanField(initial=False)
    TimeoutChooseFirm = models.BooleanField(initial=False)
    TimeoutSeeInfo = models.BooleanField(initial=False)
    TimeoutGetReady = models.BooleanField(initial=False)
    TimeoutWhyFirm = models.BooleanField(initial=False)
    TimeoutGame1Firm = models.BooleanField(initial=False)
    TimeoutResults1 = models.BooleanField(initial=False)

    see_scores_choice = models.StringField(
        widget=widgets.RadioSelect,
        choices=['Yes','No'],
        label='Before we show you the results of the contest, '
              'would you like to see the scores your opponents obtained in Part 1?')

    q6 = models.StringField()
    q7_choice = models.StringField(
        widget=widgets.RadioSelect,
        choices=['Make the same choice', 'Change my choice'],
        label="If you had the choice again, would you make the same choice?")
    q77_choice = models.StringField(
        widget=widgets.RadioSelect,
        choices=["Received information about opponents' scores before competing",
                 "Not received information about opponents' scores before competing"],
        label="If you had the choice, would you rather have ...")
    q7 = models.LongStringField(label='Why?')
    q8 = models.StringField(
        widget=widgets.RadioSelect,
        choices=['Won', 'Came Second', 'Lost'],
        label='Do you think you won, came second, or lost the contest?')

    q10 = models.PositiveIntegerField(label='Age')
    q11 = models.StringField(
        widget=widgets.RadioSelect,
        choices=['Man', 'Woman', 'Non-binary', 'Other'],
        label='Gender')
    q12 = models.LongStringField(label='Was there any part of the study that was confusing? \
        Please help us improve our study by providing feedback.',blank=True)

    B_switch_choice = models.StringField(
        widget=widgets.RadioSelect,
        choices=['Firm A', 'Firm B'])
    B_switch = models.LongStringField(label='Why?')
    debriefComments = models.LongStringField(label='Comments',blank=True)

    # Thanks to Philipp Chapkovski for the "Record time taken on waitpage" post
    Game1WaitPageSec = models.IntegerField()
    Game1FirmWaitPageSec = models.IntegerField()
    Game1ResultsWaitPageSec = models.IntegerField()

    def get_wait1(self):
        waiting_pages1 = ['Game1WaitPage']
        self.Game1WaitPageSec = sum(PageCompletion.objects.filter(participant=self.participant,
                                                          page_name__in=waiting_pages1).values_list(
            'seconds_on_page',
            flat=True))

    def get_wait1_firm(self):
        waiting_pages1_firm = ['Game1FirmWaitPage']
        self.Game1FirmWaitPageSec = sum(PageCompletion.objects.filter(participant=self.participant,
                                                          page_name__in=waiting_pages1_firm).values_list(
            'seconds_on_page',
            flat=True))

    def get_wait1_results(self):
        waiting_pages1_results = ['Results1WaitPage']
        self.Game1ResultsWaitPageSec = sum(PageCompletion.objects.filter(participant=self.participant,
                                                          page_name__in=waiting_pages1_results).values_list(
            'seconds_on_page',
            flat=True))
