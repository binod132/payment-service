from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

payments = []

@app.route('/payments', methods=['GET'])
def get_payments():
    return jsonify(payments)

@app.route('/payments', methods=['POST'])
def process_payment():
    order_id = request.json.get('order_id')
    order_response = requests.get(f'http://order-service:5000/orders/{order_id}')
    
    if order_response.status_code != 200:
        return jsonify({'error': 'Order not found'}), 404
    
    payment = {"id": len(payments) + 1, "order": order_response.json(), "status": "Processed"}
    payments.append(payment)
    return jsonify(payment), 201

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
