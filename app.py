'''
Server for our 1v1ing the bot backend using Flask
'''

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_apscheduler import APScheduler
import numpy as np
import uuid
import random
import os
from network_training import DarkChessNetwork
import torch
# import agents
from engine.agents.agent import Agent
from engine.agents.random_agents import RandomAgent, SmartRandomAgent
from engine.agents.monte_carlo_agent import MonteCarloAgent, MonteCarloTreeSearchAgent
from engine.agents.alpha_beta_agent import AlphaBetaAgent
from engine.agents.neural_network_agents import NeuralMCTSAgent
# import dark chess game
from engine.game.dark_chess import Game
# import determinizers
from engine.determinization.determinizer import IgnoranceIsBlissDeterminizer, BadDeterminizer, CheatingDeterminizer, RandomDeterminizer

# app = Flask(__name__)
app = Flask(__name__, static_folder='client/dist', static_url_path='/')
# allows react client to connect
CORS(app)

class ClientGameState:
    def __init__(self, game: Game, client_side: int, agent: Agent):
        self.game = game
        self.client_side = client_side
        self.agent = agent
        
    # get visualization for the client
    def get_frontend_visualization(self):
        return self.game.get_frontend_visualization()
    
    # only call if it is client's turn
    def get_legal_moves(self):
        return self.game.get_legal_moves()
    
    # agent makes a move
    def make_agent_move(self):
        move = self.agent.choose_move(self.game)
        self.game.take_action(move)
    
    # client makes a move, make sure they can actually do this
    def make_client_move(self, move):
        self.game.take_action(move)
    
    # 1 if client won, -1 if client lost, 0 if game is still going
    def is_game_over(self):
        res = self.game.board.game_result()
        if res == None:
            return 0
        if res == 1 and self.game.client_side == 1:
            return 1
        if res == -1 and self.game.client_side == 0:
            return 1
        return -1


active_games = {}

@app.route('/test')
def test():
    ret = {}
    ret['message'] = 'success'
    return jsonify(ret)

# starts a new game
@app.route('/start', methods=['POST'])
def startGame():
    try:
        data = request.get_json()
        # which side is the client on
        side = data['side']
        if side == 'Random':
            side = random.choice(['White', 'Black'])
        agent = data['agent']
        # determine color of agent (expects 'W' or 'B')
        agent_color = 'B' if side == 'White' else 'W'
        agent_object = None
        # possible agent strings = ['Random', 'SmartRandom', 'AlphaBeta', 'MonteCarlo', 'MonteCarloTreeSearch', 'NeuralMCTS']
        if agent == 'Random':
            agent_object = RandomAgent(name=agent, color=agent_color)
        elif agent == 'SmartRandom':
            agent_object = SmartRandomAgent(name=agent, color=agent_color)
        elif agent == 'AlphaBeta':
            agent_object = AlphaBetaAgent(name=agent, color=agent_color)
        elif agent == 'MonteCarlo':
            agent_object = MonteCarloAgent(name=agent, color=agent_color)
        elif agent == 'MonteCarloTreeSearch':
            agent_object = MonteCarloTreeSearchAgent(name=agent, color=agent_color)
        elif agent == 'NeuralMCTS':
            device = 'cpu'
            networkA = DarkChessNetwork().to(device)
            networkA.load_state_dict(torch.load("dark_chess.pth", map_location=device))
            networkA.eval()
            agent_object = NeuralMCTSAgent(name=agent, color=agent_color, network=networkA, device='cpu')
            print('a')

        determinizer = data['determinizer']
        # possible determinizers = ['IgnoranceIsBlissDeterminizer', 'BadDeterminizer', 'CheatingDeterminizer', 'RandomDeterminizer']
        if determinizer == 'IgnoranceIsBlissDeterminizer':
            determinizer_object = IgnoranceIsBlissDeterminizer()
        elif determinizer == 'BadDeterminizer':
            determinizer_object = BadDeterminizer()
        elif determinizer == 'CheatingDeterminizer':
            determinizer_object = CheatingDeterminizer()
        elif determinizer == 'RandomDeterminizer':
            determinizer_object = RandomDeterminizer()
        
        agent_object.determinizer = determinizer_object
        
        new_game_id = str(uuid.uuid4())
        client_side = 0 if side == 'Black' else 1
        # create new dark chess game
        new_game = Game(client_side=client_side)
        new_client_game = ClientGameState(new_game, client_side, agent_object)
        active_games[new_game_id] = new_client_game
        # client must know visual board and legal moves
        visual = new_client_game.get_frontend_visualization()
        legal_moves = new_client_game.get_legal_moves()
        return jsonify({
            'chess_game_id': new_game_id,
            'visual': visual,
            'legal_moves': legal_moves,
            'client_side': client_side
        })
    except Exception as e:
        print(f'error in /start: {e}')
        return jsonify({}), 500

# makes a move for client
@app.route('/makeMove', methods=['POST'])
def makeMove():
    try:
        # client sends move & their id
        data = request.get_json()
        move = data['move']
        chess_game_id = data['chess_game_id']
        client_game_state = active_games[chess_game_id]
        client_game_state.make_client_move(move)
        visual = client_game_state.get_frontend_visualization()
        legal_moves = client_game_state.get_legal_moves()
        is_game_over = client_game_state.is_game_over()
        return jsonify({
            'visual': visual,
            'legal_moves': legal_moves,
            'is_game_over': is_game_over
        })
    except Exception as e:
        print(f'error in /makeMove: {e}')
        return jsonify({}), 500

# makes a move for the server
@app.route('/makesServerMove', methods=['POST'])
def makeServerMove():
    try:
        data = request.get_json()
        chess_game_id = data['chess_game_id']
        client_game_state = active_games[chess_game_id]
        move = client_game_state.make_agent_move()
        visual = client_game_state.get_frontend_visualization()
        legal_moves = client_game_state.get_legal_moves()
        is_game_over = client_game_state.is_game_over()
        return jsonify({
            'visual': visual,
            'legal_moves': legal_moves,
            'is_game_over': is_game_over
        })
    except Exception as e:
        print(f'error in /makesServerMove: {e}')
        return jsonify({}), 500
    
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(debug=True)
    