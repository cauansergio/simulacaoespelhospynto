from flask import Flask, render_template, jsonify, request
import numpy as np
import os

app = Flask(__name__)

def calcular_imagens(theta_deg, obj_radius, obj_angle_deg):
    """Calcula as imagens formadas pelos espelhos"""
    # Converter para radianos
    theta = np.radians(theta_deg)
    obj_angle = np.radians(obj_angle_deg)
    
    # Coordenadas do objeto
    obj_x = obj_radius * np.cos(obj_angle)
    obj_y = obj_radius * np.sin(obj_angle)
    
    # Calcular número teórico
    n = theta_deg
    if n == 0:
        formula = "Espelhos paralelos: infinitas imagens"
        N_theory = 20  # limite prático para visualização
    elif 360 % n == 0:
        N_theory = int(360 / n) - 1
        formula = f"N = 360°/{n}° - 1 = {N_theory}"
    else:
        N_theory = int(360 / n)
        formula = f"N ≈ 360°/{n}° ≈ {N_theory}"
    
    # Gerar imagens
    images = []
    images.append({"x": float(obj_x), "y": float(obj_y), "type": "objeto"})
    
    # Primeiro espelho (eixo X)
    mirror1_angle = 0
    # Segundo espelho
    mirror2_angle = theta
    
    generated_positions = set()
    generated_positions.add((round(obj_x, 3), round(obj_y, 3)))
    
    # Limitar número máximo de imagens para performance
    max_images = min(50, N_theory + 20)
    
    # Para cada sequência de reflexões
    for sequence_length in range(1, 7):  # Até 6 reflexões
        if len(images) >= max_images:
            break
            
        # Gerar sequências binárias
        sequences = []
        for i in range(2**sequence_length):
            seq = []
            for j in range(sequence_length):
                seq.append((i >> j) & 1)
            sequences.append(seq)
        
        for seq in sequences:
            if len(images) >= max_images:
                break
                
            current_angle = obj_angle
            for mirror in seq:
                if mirror == 0:
                    current_angle = 2 * mirror1_angle - current_angle
                else:
                    current_angle = 2 * mirror2_angle - current_angle
            
            # Normalizar
            current_angle = current_angle % (2 * np.pi)
            if current_angle > np.pi:
                current_angle -= 2 * np.pi
            
            # Calcular posição
            img_x = obj_radius * np.cos(current_angle)
            img_y = obj_radius * np.sin(current_angle)
            
            pos_key = (round(img_x, 3), round(img_y, 3))
            
            if pos_key not in generated_positions:
                generated_positions.add(pos_key)
                images.append({
                    "x": float(img_x), 
                    "y": float(img_y), 
                    "type": "imagem",
                    "sequence": len(images)  # número da imagem
                })
    
    return images, formula, len(images) - 1

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        data = request.json
        theta_deg = float(data.get('theta', 60))
        obj_radius = float(data.get('radius', 3.0))
        obj_angle_deg = float(data.get('angle', 30))
        
        # Validar entradas
        theta_deg = max(1, min(270, theta_deg))
        obj_radius = max(0.5, min(4.5, obj_radius))
        obj_angle_deg = obj_angle_deg % 360
        
        images, formula, num_imagens = calcular_imagens(theta_deg, obj_radius, obj_angle_deg)
        
        # Calcular coordenadas dos espelhos
        theta_rad = np.radians(theta_deg)
        espelho1 = [{"x": 0, "y": 0}, {"x": 5, "y": 0}]
        espelho2 = [
            {"x": 0, "y": 0}, 
            {"x": float(5*np.cos(theta_rad)), "y": float(5*np.sin(theta_rad))}
        ]
        
        return jsonify({
            "success": True,
            "images": images,
            "formula": formula,
            "num_imagens": num_imagens,
            "espelho1": espelho1,
            "espelho2": espelho2,
            "theta": theta_deg,
            "obj_radius": obj_radius,
            "obj_angle": obj_angle_deg,
            "explicacao": f"Com espelhos a {theta_deg}°, cada reflexão muda o ângulo em {2*theta_deg}°"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/health')
def health():
    """Endpoint de saúde para o Render"""
    return jsonify({"status": "healthy", "service": "simulacao-espelhos"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)