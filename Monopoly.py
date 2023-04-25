# Mehrad Hajati

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# From an array of stats from many games, work up all the data we need
def bootstrap_stats(game_array, degree):

    # collect these values from each randomly sampled game - to calculate means in return
    bootstrapped_turns = []
    bootstrapped_trips_until_props_bought = []

    # count how many games end without all the properties being bought
    games_ended_without_all_props_bought = 0
    
    # bootstrap a number of times defined by the degree of bootstrapping
    for i in range (degree):
        
        # create an array of randomly sampled (with replacement) indices
        # amount equal to the number in the original array
        random_sample_indices = np.random.randint(0, len(game_array), len(game_array))

        # for each random index selected, do all the work for the stats for that game
        for j in range (len(random_sample_indices)):

            # add number of turns passed from this game, use the randomly sampled ones later to calculate a mean
            bootstrapped_turns.append(game_array[random_sample_indices[j]].num_turns_passed)

            # some games end without all the properties being bought - count them so we can get a percentage
            if game_array[random_sample_indices[j]].trip_last_property_bought == -1:
                games_ended_without_all_props_bought +=1

            # add number of trips for games where all properties were bought to array to calculate the mean later
            else:
                bootstrapped_trips_until_props_bought.append(game_array[random_sample_indices[j]].trip_last_property_bought)

    # report a percentage of games where the properties were all bought
    percent_game_all_props_bought = 100 * (1 - (games_ended_without_all_props_bought / (len(game_array) * degree)))
        
    # return all stats
    return np.mean(bootstrapped_turns), np.mean(bootstrapped_trips_until_props_bought), percent_game_all_props_bought

class Stats:
    def __init__(self, winner, num_turns_passed, turn_last_property_bought, num_trips_around, trip_last_property_bought):
        self.winner = winner
        self.num_turns_passed = num_turns_passed
        self.turn_last_property_bought = turn_last_property_bought
        self.num_trips_around = num_trips_around
        self.trip_last_property_bought = trip_last_property_bought

# keeps track of type of space, cost to purchase, and base rent
# name field isn't used, it just helped us keep track of what Space is which
# also tracks current owner, and if the Space was ever purchased
class Space:
    def __init__(self, kind, name, cost, rent, colour):
        self.kind = kind
        self.name = name
        self.cost = cost
        self.rent = rent
        self.colour = colour
        self.owned_by = None
        self.ever_bought = False

# Keeps track of available money, current space Player is on,
# and if they are still in the game, and jail sentence in turns
class Player:
    def __init__(self):
        self.money = 1500
        self.space = 0
        self.eliminated = False
        self.sentence = 0

# class that contains all the data and methods necessary to run one game of Monopoly
class Game:
    def __init__(self, num_players, properties_auctioned, free_parking_gives_500, rounds_before_jacking_rent):
        # list of players is by default empty, it is the turn of the 0th player, and no turns
        # have passed at the beginning of the game, no trips have been made around the board
        # rent level determines which rent we charge for properties
        self.players = []
        self.curr_turn = 0
        self.num_turns_passed = 0
        self.num_trips_around = 0
        self.rent_level = 0
        self.rounds_before_jacking_rent = rounds_before_jacking_rent 

        # -1 is a dummy value for the winner and turn  and trip around which last property was
        # purchased for the first time,  which is undertermined at start of game
        self.turn_last_property_bought = -1
        self.trip_last_property_bought = -1
        self.winner = -1
        
        # set up fresh board
        self.board = makeNewBoard()

        # add players up to the specified amount
        for i in range (num_players):
            new_player = Player()
            self.players.append(new_player)

        # set optional rules
        self.properties_auctioned = properties_auctioned
        self.free_parking_gives_500 = free_parking_gives_500

    # play throught the game
    def run(self):

        # continue as long as we have no winner declared
        while(self.winner == -1):

            # bump up rent tier if enough rounds have passed for each player
            if (self.num_turns_passed >= self.rounds_before_jacking_rent and self.num_turns_passed % (len(self.players) * self.rounds_before_jacking_rent)  == 0 and self.rent_level < 5):
                self.rent_level += 1
                
            curr_player = self.players[self.curr_turn]

            # only interested if the player whose turn it is is still in the game
            if (curr_player.eliminated == False):

                # if they still have turns in Jail
                if curr_player.sentence > 0:

                    # if they can pay the fine right away, they pay it and get out of jail
                    if (curr_player.money > 50):
                        curr_player.money -= 50
                        curr_player.sentence = 0

                    else:
                        # decrease the turns remaining in Jail by 1
                        curr_player.sentence -= 1

                    # if they have served their sentence
                    if curr_player.sentence == 0:

                        # the player pays the 50 dollar fine, is eliminated if they cannot pay
                        curr_player.money -= 50
                        if curr_player.money < 0:
                            self.eliminate (curr_player, "bank")
        
                # roll your first pair of dice
                doubles, roll_total = rollTwoDice()

                # if you rolled doubles you can immediately leave jail without servign sentence
                if doubles:
                    curr_player.sentence = 0

                # can move, but only if no sentence in Jail
                if curr_player.sentence == 0:
                    self.move_player(curr_player, roll_total)

                    # if your first roll was doubles you can roll again
                    if doubles:
                        doubles,roll_total = rollTwoDice()
                        self.move_player(curr_player, roll_total)

                        # if your second roll was doubles, you can roll a third time
                        if doubles:
                            doubles,roll_total = rollTwoDice()

                            # third doubles in a row - go to jail
                            if doubles:
                                self.go_to_jail(curr_player)

                            # otherwise move normally
                            else:
                                self.move_player(curr_player, roll_total)          

            # go to next turn
            self.num_turns_passed += 1
            self.curr_turn = (self.curr_turn + 1) % len(self.players)

        # game ended, return stats
        return self.winner, self.num_turns_passed, self.turn_last_property_bought, self.num_trips_around, self.trip_last_property_bought

    # player is removed from game, additional parameter 'owing_who'
    # says if the creditor they lost to is the Bank or another player
    def eliminate(self, player, owing_who):
        player.eliminated = True
        player.money = 0

        # count how many players in the game were eliminated
        how_many_eliminated = 0
        for i in range(len(self.players)):
            if self.players[i].eliminated:
                how_many_eliminated += 1

        # if all but one player was eliminated, that player is the winner
        if how_many_eliminated >= (len(self.players) - 1):
            for i in range(len(self.players)):
                if not self.players[i].eliminated:
                    self.winner = i

        # otherwise if the game is still going, handle the
        # distribution of the eliminated player's assets 
        else:
            # if they owed the bank, release their properties and auction them off
            if owing_who == "bank":
                for i in range (len(self.board)):
                    if self.board[i].owned_by == player:
                        self.board[i].owned_by = None
                        self.auction(self.board[i])

            # if they were eliminated because they could not pay another player
            # give that player all of their properties
            else:
                for i in range (len(self.board)):
                    if self.board[i].owned_by == player:
                        self.board[i].owned_by = owing_who
            
    # count how many railroads are owned by a given player
    def railroads_owned(self, player):
        count = 0

        # Reading Railroad
        if self.board[5].owned_by == player:
            count += 1

        # Pennsylvania Railroad
        if self.board[15].owned_by == player:
            count += 1

        # B&O Railroad
        if self.board[25].owned_by == player:
            count += 1

        # Short Line
        if self.board[35].owned_by == player:
            count += 1
            
        return count

    # count how many utilities are owned by a given player
    def utilities_owned(self, player):
        count = 0

        # Electric Company
        if self.board[12].owned_by == player:
            count +=1

        # Water Works
        if self.board[28].owned_by == player:
            count +=1
            
        return count

    # given a total from a dice roll, move the player that rolled it
    def move_player(self, player, roll_total):

        # if the new space has a lower index than the one you started at, you hav
        # landed on or passed GO.   This will always be true because you can't go
        # all the way around the board in one roll
        if (player.space + roll_total) % 40 < player.space:
            player.money += 200
            self.num_trips_around +=1
            
        player.space = (player.space + roll_total) % 40

        # handle landing on the space you've move to
        self.land(player)

    # determine if all spaces sharing a colour with a given space are owned by the same player
    def colour_monopoly(self, space):
        owner = space.owned_by
        for i in range (len(self.board)):
            if self.board[i].colour == space.colour and self.board[i].owned_by != owner:
                return False
        return True

    # a given player pays rent at a specific space
    def player_pays_rent(self, player, space):
        # initialize a payment amount before calculating it
        payment = 0

        # for properties, the amount to be paid is the rent
        # unless the owning player owns all of the same colour, then then can charge twice the rent
        if space.kind == "property":
            if self.colour_monopoly(space):
                payment = 2 * space.rent[self.rent_level]
            else:
                payment = space.rent[self.rent_level]

        # for railroads, the amount to be paid depends on how many railroads the owner owns
        # 25 for 1, 50 for 2, 100 for 3, 200 for 4
        elif space.kind == "railroad":
            payment = 25 * (2**(self.railroads_owned(space.owned_by) - 1))

        # for utilities, the amount to be paid depends on how many utilities the owner owns
        # 4 times a dice roll if one, 10 times a dice roll if both
        elif space.kind == "utility":
            if self.utilities_owned(space.owned_by) == 1:
                payment = rollDice() * 4
            elif self.utilities_owned(space.owned_by) == 2:
                payment = rollDice() * 10

        # if the player can pay the rent they give the money to the owner of the space
        if player.money > payment:
            player.money -= payment
            space.owned_by.money += payment

        # if they can't, they give what they can, and the player is eliminated
        else:
            space.owned_by.money += player.money
            self.eliminate(player, space.owned_by)

    # purchasing a property
    def player_buys_property(self, player, space):
        player.money -= space.cost
        space.owned_by = player
        space.ever_bought = True

        # if we have not yet found the turn where the last property was bought for the first time,
        # and this was the last unbought property, this was that turn
        if self.turn_last_property_bought == -1 and self.all_props_owned():
            self.turn_last_property_bought = self.num_turns_passed
            self.trip_last_property_bought = self.num_trips_around
            

    # send a player to the Jail space with a 3 turn sentence
    def go_to_jail(self, player):
            player.space = 10
            player.sentence = 3

    # auction a given space
    def auction(self, space):
        # make a list of players that can afford the space
        players_who_can_afford = []
        for i in range (len(self.players)):
            if self.players[i].eliminated == False and self.players[i].money > space.cost:
                players_who_can_afford.append(self.players[i])

        # if there is at least onem pick one randomly and they buy it
        if len(players_who_can_afford) > 0:
            sell_to = np.random.randint(0,len(players_who_can_afford))
            self.player_buys_property(players_who_can_afford[sell_to], space)

    # handles what happens when the player lands on each kind of space
    def land(self, player):
        space = self.board[player.space]

        # landed on "Free Parking" - give 500 if optional rule on
        if (space.kind == "parking" and self.free_parking_gives_500):
            player.money += 500

        # landed on either "Tax" space - eliminate player if they can't pay
        elif (space.kind == "tax"):
            if player.money > space.cost:
                player.money -= space.cost
            else:
                self.eliminate(player, "bank")

        # landed on "Go to Jail"
        elif (space.kind == "goto"):
            self.go_to_jail(player)

        # landed on an unowned property
        elif (space.owned_by == None and (space.kind == "property" or space.kind == "utility" or space.kind == "railroad")):

            # can afford to buy without hitting 0 dollars
            if player.money > space.cost:
                self.player_buys_property(player, space)

            # if property auctioning rule on, auction it
            elif self.properties_auctioned:
                self.auction(space)

        # if landed on owned space that is not owned but the player - player pays rent to owner
        elif (space.owned_by != None and space.owned_by != player):
            self.player_pays_rent(player, space)

    # checks if all properties have been bought at least once
    #utilities and  railroads are ownable properties, but have another type
    def all_props_owned(self):
        for i in range (len(self.board)):
            if (self.board[i].kind == "property" or self.board[i].kind == "railroad" or
               self.board[i].kind == "utility") and self.board[i].ever_bought == False:
                   return False
        return True
   
# roll a single dice 1 to 6
def rollDice():
    return np.random.randint(1,7)

# roll two 6-sided die  and return whether or not they were doubles, and the total
def rollTwoDice():
    doubles = False
    roll1 = rollDice()
    roll2 = rollDice()
    if roll1 == roll2:
        doubles = True
    return doubles, (roll1 + roll2)

# build a standard US version Monopoly board
# making the board fresh makes it easier to reset the properties of each Space
def makeNewBoard():

    med_ave = Space("property","Mediterranean Avenue", 60, [2, 10, 30, 90, 160, 250], "brown")
    balt_ave = Space("property","Baltic Avenue", 60, [4, 20, 60, 180, 320, 450], "brown")

    or_ave = Space("property", "Oriental Avenue", 100, [6, 30, 90, 270, 400, 550], "lightblue")
    verm_ave = Space("property", "Vermont Avenue", 100, [6, 30, 90, 270, 400, 550], "lightblue")
    conn_ave = Space("property", "Conneticut Avenue", 120, [8, 40, 100, 300, 450, 600], "lightblue")

    st_ch_place = Space("property", "St. Charles Place", 140, [10, 50, 150, 450, 625, 750], "pink")
    states_ave = Space("property", "States Avenue", 140, [10, 50, 150, 450, 625, 750], "pink")
    vir_ave = Space("property", "Virginia Avenue", 160, [12, 60, 180, 500, 700, 900], "pink")

    st_jam_place = Space("property", "St. James Place", 180, [14, 70, 200, 550, 750, 950], "orange")
    tenn_ave = Space("property", "Tennessee Avenua", 180, [14, 70, 200, 550, 750, 950], "orange")
    ny_ave = Space("property", "New York Avenue", 200, [16, 80, 220, 600, 800, 1000], "orange")

    kent_ave = Space("property", "Kentucky Avenue", 220, [18, 90, 250, 700, 875, 1050], "red")
    ind_ave = Space("property", "Indiana Avenue", 220, [18, 90, 250, 700, 875, 1050], "red")
    ill_ave = Space("property", "Illinois Avenue", 240, [20, 100, 300, 750, 925, 1100], "red")

    atl_ave = Space("property", "Atlantic Avenue", 260, [22, 110, 330, 800, 975, 1150], "yellow")
    vent_ave = Space("property", "Ventnor Avenue", 260, [22, 110, 330, 800, 975, 1150], "yellow")
    marv_gard = Space("property", "Marvin Gardens", 280, [24, 120, 360, 850, 1025, 1200], "yellow")

    pac_ave = Space("property", "Pacific Avenue", 300, [26, 130, 390, 900, 1100, 1275], "green")
    nc_ave = Space("property", "North Carolina Avenue", 300, [26, 130, 390, 900, 1100, 1275], "green")
    penn_ave = Space("property", "Pennsylvania Avenue", 320, [28, 150, 450, 1000, 1200, 1400], "green")

    park_place = Space("property", "Park Place", 350, [35, 175, 500, 1100, 1300, 1500], "darkblue")
    boardwalk = Space("property", "Boardwalk", 400, [50, 200, 600, 1400, 1700, 2000], "darkblue")

    read_rail = Space("railroad", "Reading Railroad", 200, [25], "none")
    penn_rail = Space("railroad", "Pennsylvania Railroad", 200, [25], "none")
    bo_rail = Space("railroad", "B&O Railroad", 200 , [25], "none")
    short_rail = Space("railroad", "Short Line", 200, [25], "none")
    elec_util = Space("utility", "Electric Company", 150, [0], "none")
    water_util = Space("utility", "Water Works", 150, [0], "none")

    # other spaces
    go = Space("go","GO", 0, [0], "none")
    inc_tax = Space("tax", "Income Tax", 200, [0], "none")
    lux_tax = Space("tax", "Luxury Tax", 100, [0], "none")
    comm_chest = Space("chest", "Community Chest", 0, [0], "none")
    chance = Space("chance", "Chance", 0, [0], "none")
    jail = Space("jail", "In Jail", 0, [0], "none") 
    free_park = Space("parking", "Free Parking", 0, [0], "none")
    goto = Space("goto", "Go To Jail", 0, [0], "none")
    
    # hard code array to match standard US version Monopoly board
    board = [go, med_ave, comm_chest, balt_ave, inc_tax,
             read_rail, or_ave, chance, verm_ave, conn_ave,
             jail, st_ch_place, elec_util, states_ave, vir_ave,
             penn_rail, st_jam_place, comm_chest, tenn_ave, ny_ave,
             free_park, kent_ave, chance, ind_ave, ill_ave,
             bo_rail, atl_ave, vent_ave, water_util, marv_gard,
             goto, pac_ave, nc_ave, comm_chest, penn_ave,
             short_rail, chance, park_place, lux_tax, boardwalk]
    
    return board

#####################
###  SIMULATIONS  ###
#####################
num_sims_per_ruleset = 500
num_players = 15
how_much_to_bootstrap = 10000
rounds_before_rent_increase = 10

### GAME TYPE 1 ###
# no optional rules
# properties auctioned, free parking does not give 500 dollars
game_type_1_stats = []
game_type_1_winners = []
for i in range(num_sims_per_ruleset):
  
    game = Game(num_players, True, False, rounds_before_rent_increase)

    # run game and get stats
    winner, num_turns_passed, turn_last_property_bought, num_trips_around, trip_last_property_bought = game.run()
    stats = Stats(winner, num_turns_passed, turn_last_property_bought, num_trips_around, trip_last_property_bought)

    game_type_1_stats.append(stats)
    game_type_1_winners.append(winner)

game_type_1_turns_passed, game_type_1_prop_bought, percent_type_1_games_ended_with_all_props_bought = bootstrap_stats(game_type_1_stats, how_much_to_bootstrap)

plt.xticks(ticks=[0,1,2,3], labels=[1,2,3,4])
plt.hist(game_type_1_winners, bins=num_players, edgecolor='black')
plt.xlabel("Winner (Player)")
plt.ylabel("# times won")
plt.show()

print("GAME TYPE 1 - no optional rules")
print("MEAN TURNS PASSED: " + str(game_type_1_turns_passed))
print("MEAN TURN LAST PROP. BOUGHT: " + str(game_type_1_prop_bought))
print("PERCENT GAMES ALL PROPS BOUGHT: " + str(percent_type_1_games_ended_with_all_props_bought))
print()

### GAME TYPE 2 ###
# rule for part c.i active
# properties auctioned, free parking gives 500 dollars
game_type_2_stats = []
game_type_2_winners = []
for i in range(num_sims_per_ruleset):
    game = Game(num_players, True, True, rounds_before_rent_increase)
    
    # run game and get stats
    winner, num_turns_passed, turn_last_property_bought, num_trips_around, trip_last_property_bought = game.run()
    stats = Stats(winner, num_turns_passed, turn_last_property_bought, num_trips_around, trip_last_property_bought)

    game_type_2_stats.append(stats)
    game_type_2_winners.append(winner)

game_type_2_turns_passed, game_type_2_prop_bought, percent_type_2_games_ended_with_all_props_bought = bootstrap_stats(game_type_2_stats, how_much_to_bootstrap)

plt.xticks(ticks=[0,1,2,3], labels=[1,2,3,4])
plt.hist(game_type_2_winners, bins=num_players, edgecolor='black')
plt.xlabel("Winner (Player)")
plt.ylabel("# times won")
plt.show()

print("GAME TYPE 2 - Free Parking nets you 500$")
print("MEAN TURNS PASSED: " + str(game_type_2_turns_passed))
print("MEAN TURN LAST PROP. BOUGHT: " + str(game_type_2_prop_bought))
print("PERCENT GAMES ALL PROPS BOUGHT: " + str(percent_type_2_games_ended_with_all_props_bought))
print()

### GAME TYPE 3 ###
# rule for part c.ii active
# properties are not auctioned, free parking does not give 500 dollars
game_type_3_stats = []
game_type_3_winners = []
for i in range(num_sims_per_ruleset):
    game = Game(num_players, False, False, rounds_before_rent_increase)

    # run game and get stats
    winner, num_turns_passed, turn_last_property_bought, num_trips_around, trip_last_property_bought = game.run()
    stats = Stats(winner, num_turns_passed, turn_last_property_bought, num_trips_around, trip_last_property_bought)

    game_type_3_stats.append(stats)
    game_type_3_winners.append(winner)

game_type_3_turns_passed, game_type_3_prop_bought, percent_type_3_games_ended_with_all_props_bought = bootstrap_stats(game_type_3_stats, how_much_to_bootstrap)

plt.xticks(ticks=[0,1,2,3], labels=[1,2,3,4])
plt.hist(game_type_3_winners, bins=num_players, edgecolor='black')
plt.xlabel("Winner (Player)")
plt.ylabel("# times won")
plt.show()

print("GAME TYPE 3 - Properties are not aucitoned")
print("MEAN TURNS PASSED: " + str(game_type_3_turns_passed))
print("MEAN TURN LAST PROP. BOUGHT: " + str(game_type_3_prop_bought))
print("PERCENT GAMES ALL PROPS BOUGHT: " + str(percent_type_3_games_ended_with_all_props_bought))
print()

### GAME TYPE 4 ###
# both rules at once
# properties are not auctioned, free parking gives 500 dollars
game_type_4_stats = []
game_type_4_winners = []
for i in range(num_sims_per_ruleset):
    game = Game(num_players, False, True, rounds_before_rent_increase)

    # run game and get stats
    winner, num_turns_passed, turn_last_property_bought, num_trips_around, trip_last_property_bought = game.run()
    stats = Stats(winner, num_turns_passed, turn_last_property_bought, num_trips_around, trip_last_property_bought)

    game_type_4_stats.append(stats)
    game_type_4_winners.append(winner)

game_type_4_turns_passed, game_type_4_prop_bought, percent_type_4_games_ended_with_all_props_bought = bootstrap_stats(game_type_4_stats, how_much_to_bootstrap)

plt.xticks(ticks=[0,1,2,3], labels=[1,2,3,4])
plt.hist(game_type_4_winners, bins=num_players, edgecolor='black')
plt.xlabel("Winner (Player)")
plt.ylabel("# times won")
plt.show()

print("GAME TYPE 4 - both optional rules included")
print("MEAN TURNS PASSED: " + str(game_type_4_turns_passed))
print("MEAN TURN LAST PROP. BOUGHT: " + str(game_type_4_prop_bought))
print("PERCENT GAMES ALL PROPS BOUGHT: " + str(percent_type_4_games_ended_with_all_props_bought))
print()
