from flask_cors import CORS
from flask import Flask, jsonify, request, send_from_directory

from blockchain import Blockchain
from wallet import Wallet


app = Flask(__name__)
wallet = Wallet()
blockchain = Blockchain(wallet.public_key)
CORS(app)


@app.route('/', methods=['GET'])
def get_ui():
    return send_from_directory('UI', 'node.html')


@app.route('/wallet', methods=['POST'])
def create_keys():
    global blockchain
    wallet.create_keys()
    if wallet.save_keys():
        blockchain = Blockchain(wallet.public_key)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Saving keys failed'
        }
        return jsonify(response), 500


@app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key)
        response = {
            'public_key': wallet.public_key,
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Loading keys failed'
        }
        return jsonify(response), 500


@app.route('/chain', methods=['GET'])
def get_chain():
    chain = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain]
    for block in dict_chain:
        block['transactions'] = [
            tx.__dict__ for tx in block['transactions']]
    return jsonify(dict_chain), 200


@app.route('/balance', methods=['GET'])
def balance():
    balance = blockchain.get_balance()
    if balance != None:
        response = {
            'message': 'Succesfully fecthed balance',
            'balance': balance
        }
        return jsonify(response), 200
    else:
        response = {
            'message': 'Loading balance failed.',
            'wallet_available': wallet.public_key != None
        }
        return jsonify(response), 500


@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key == None:
        response = {
            'message': 'No wallet found'
        }
        return jsonify(response), 400
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found.'
        }
        return jsonify(response), 400
    req_fields = ['recipient', 'amount']
    if not all(field in values for field in req_fields):
        response = {
            'message': 'required data missing.'
        }
        return jsonify(response), 400
    recipient = values['recipient']
    amount = values['amount']
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    if blockchain.add_transaction(recipient, wallet.public_key, signature, amount):
        response = {
            'message': 'Succesfully added transaction',
            'transaction': {
                'sender': wallet.public_key,
                'recipient': recipient,
                'amount': amount,
                'signature': signature
            },
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201

    else:
        response = {
            'message': 'Creating transaction failed.'
        }
        return jsonify(response), 500


@app.route('/transactions', methods=['GET'])
def get_transaction():
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.__dict__ for tx in transactions]
    return jsonify(dict_transactions), 200


@app.route('/node', methods=['Post'])
def add_node():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found.'
        }
        return jsonify(response), 400
    if 'node' not in values:
        response = {
            'message': 'No node found.'
        }
        return jsonify(response), 400
    node = values.get('node')
    blockchain.add_peer(node)
    response = {
        'message': 'Node added!',
        'all_nodes': list(blockchain.get_peers())
    }
    return jsonify(response), 201


@app.route('/node/<node_url>', methods=['DELETE'])
def remove_node(node_url):
    if node_url == '' or node_url == None:
        response = {
            'message': 'No node found.'
        }
        return jsonify(response), 400
    blockchain.remove_peer(node_url)
    response = {
        'message': 'Node removed!',
        'all_nodes': list(blockchain.get_peers())
    }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_peers():
    nodes = blockchain.get_peers()
    response = {
        'all_nodes': list(blockchain.get_peers())
    }
    return jsonify(response), 200


@app.route('/mine', methods=['POST'])
def mine():
    block = blockchain.mine_block()
    if block != None:
        dict_block = block.__dict__.copy()
        dict_block['transactions'] = [
            tx.__dict__ for tx in dict_block['transactions']]
        response = {
            'message': 'Block added successfully',
            'block': dict_block,
            'balance': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Adding a block failed.',
            'wallet_available': wallet.public_key != None
        }
        return response, 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)