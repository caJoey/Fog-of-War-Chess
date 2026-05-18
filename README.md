# Dark Chess Agents

![](/github_pic1.PNG)

## Website Link

https://fog-of-war-chess.azurewebsites.net/

## Current Features 

- 5x5 mini chess board
- Basic game state representation
- Simplified movement rules
- Fog-of-war style visibility function
- Random agent
- Minimax agent
- MCTS draft agent
- Evaluation script for head-to-head matches

## Minichess Implementation

https://github.com/patrik-ha/explainable-minichess or [https://arxiv.org/abs/2211.05500](https://arxiv.org/abs/2211.05500)

This is the original minichess implementation we modified to turn it into dark chess. Uses the following rules:

## Rules

The following are the deviations away from normal 8x8 chess:

- 5x5 board
- Win condition is taking the enemies king
- No pawn double-move or castling (AISE / Italian Heterodox Chess Association rules)
- Promotions still allowed

## Running Website Locally

1. Clone repository

2. Create a Python venv (optional)

- python3 -m venv .venv

3. Activate venv (optional)

- source .venv/bin/activate

4. Install requirements in root

- pip install -r requirements.txt

5. Run the app

- python3 app.py

6. Setup frontend

- cd client

7. Install dependencies

- npm install

8. start dev server

- npm run dev

Then the website should be available at http://localhost:5173/.

![](/github_pic2.PNG)
