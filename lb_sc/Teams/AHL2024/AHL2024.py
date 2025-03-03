import math
from datetime import datetime

def parse_match_scores(score1, score2):
    """Convert numerical scores to win margin for ELO calculation"""
    if score1 > score2:
        if score1 - score2 == 1:
            return 0.6  # Close match
        elif score1 - score2 == 2:
            return 0.8  # Clear win
        else:
            return 1.0  # Dominant win
    else:
        return 0.0

def parse_group_stage(matches_data):
    """Parse group stage matches from tournament data"""
    parsed_matches = []
    for match in matches_data:
        team1, score1, team2, score2 = match
        result = parse_match_scores(score1, score2)
        parsed_matches.append((team1, team2, result))
    return parsed_matches

def calculate_elo_change(rating_a, rating_b, score_a, k_factor=64):
    """Calculate ELO change with increased K-factor and score weighting"""
    expected_a = 1 / (1 + math.pow(10, (rating_b - rating_a) / 300))
    change = k_factor * (score_a - expected_a)
    return change

def process_match(teams, team_a, team_b, score_a, k_factor=64):
    """Process a single match with weighted scores"""
    if team_a not in teams:
        teams[team_a] = 1000
    if team_b not in teams:
        teams[team_b] = 1000
    
    if k_factor > 64:
        actual_k = k_factor * 1.5
    else:
        actual_k = k_factor
    
    elo_change = calculate_elo_change(teams[team_a], teams[team_b], score_a, actual_k)
    teams[team_a] += elo_change
    teams[team_b] -= elo_change

def calculate_tournament_elos(matches, playoff_k_factor=96):
    """Calculate ELO ratings with different K-factors for playoffs"""
    teams = {}
    
    group_matches = matches[:-8]
    playoff_matches = matches[-8:]
    
    for team_a, team_b, score_a in group_matches:
        process_match(teams, team_a, team_b, score_a)
    
    for team_a, team_b, score_a in playoff_matches:
        process_match(teams, team_a, team_b, score_a, playoff_k_factor)
    
    return teams

def generate_output(ratings, filename):
    """Generate formatted output and SQL statements"""
    # Sort teams by rating
    sorted_teams = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    
    # Create output string
    output = []
    output.append("Final ELO Ratings:")
    output.append("================")
    output.append("Rank | Team         | Rating")
    output.append("-" * 35)
    
    # Add formatted results
    for rank, (team, rating) in enumerate(sorted_teams, 1):
        output.append(f"{rank:4d} | {team:<12} | {int(rating):4d}")
    
    output.append("\n\n-- SQL Insert Statements:")
    output.append("-- Generated on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Add SQL statements
    output.append("\n-- Delete existing data")
    output.append("DELETE FROM results;")
    output.append("\n-- Insert new data")
    for rank, (team, rating) in enumerate(sorted_teams, 1):
        sql = f"INSERT INTO results (rank, team_name, elo) VALUES ({rank}, '{team}', {int(rating)});"
        output.append(sql)
    
    # Write to file
    with open(filename, 'w') as f:
        f.write('\n'.join(output))
    
    print(f"Results have been written to {filename}")

# Main execution
if __name__ == "__main__":
    # Tournament match data
    group_matches_data = [
        # Round 1
        ("Rapture", 2, "Loyalty", 1),
        ("Renaissance", 1, "Eternal", 2),
        ("Cynic", 0, "Infinity", 2),
        ("Eclipse", 0, "Oracle", 2),
        ("Kitchaze", 1, "Eunoia", 2),
        ("Misery", 0, "Calamity", 2),
        ("Severance", 2, "The Valentines", 1),
        ("Catalyst", 1, "Elysium", 2),
        
        # Round 2
        ("Eternal", 2, "Rapture", 0),
        ("Loyalty", 1, "Renaissance", 2),
        ("Oracle", 2, "Cynic", 0),
        ("Infinity", 2, "Eclipse", 1),
        ("Calamity", 2, "Kitchaze", 0),
        ("Eunoia", 2, "Misery", 1),
        ("Elysium", 2, "Severance", 0),
        ("The Valentines", 0, "Catalyst", 2),
        
        # Round 3
        ("Renaissance", 1, "Rapture", 2),
        ("Loyalty", 0, "Eternal", 2),
        ("Eclipse", 2, "Cynic", 0),
        ("Infinity", 1, "Oracle", 2),
        ("Misery", 2, "Kitchaze", 1),
        ("Eunoia", 1, "Calamity", 2),
        ("Catalyst", 0, "Severance", 2),
        ("The Valentines", 2, "Elysium", 0)
    ]

    playoff_matches_data = [
        ("Eternal", 3, "Severance", 1),
        ("Calamity", 3, "Infinity", 0),
        ("Oracle", 3, "Eunoia", 1),
        ("Elysium", 3, "Rapture", 1),
        ("Eternal", 2, "Calamity", 3),
        ("Oracle", 0, "Elysium", 3),
        ("Calamity", 3, "Elysium", 1),
        ("Calamity", 1, "Elysium", 4)
    ]

    # Parse and calculate
    all_matches = (
        parse_group_stage(group_matches_data) + 
        parse_group_stage(playoff_matches_data)
    )
    
    # Calculate final ratings
    ratings = calculate_tournament_elos(all_matches)
    
    # Generate output file
    generate_output(ratings, 'tournament_results.txt')