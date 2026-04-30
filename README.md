# 🌿 Monitor de Saúde de Plantas

Aplicação de **Visão Computacional clássica** que analisa em tempo real a cor das folhas de uma planta para estimar seu estado de saúde — sem nenhum modelo de Inteligência Artificial ou Machine Learning.

---

## 📌 Problema Resolvido

Identificar quando uma planta está com deficiência nutricional, hídrica ou doença é um processo que exige atenção diária. Folhas saudáveis são verdes; folhas estressadas amarelam; folhas doentes escurecem ou amarronzam. Esta aplicação automatiza essa análise usando apenas a câmera do computador, calculando a proporção de pixels saudáveis (verdes) em relação ao total foliar detectado e exibindo um diagnóstico em tempo real.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Finalidade |
|---|---|---|
| Python | 3.9+ | Linguagem principal |
| OpenCV | 4.8+ | Processamento de imagem e vídeo |
| NumPy | 1.24+ | Operações matriciais e criação de kernels |

---

## ⚙️ Instalação e Execução

**Pré-requisito:** Python 3.9 ou superior com webcam conectada.

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/plant-health-monitor.git
cd plant-health-monitor

# 2. (Opcional) Ambiente virtual
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
.venv\Scripts\activate          # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute
python main.py
```

Aponte a câmera para uma planta e pressione **`Q`** para encerrar.

---

## 🔍 Técnicas de Visão Computacional Utilizadas

Todo o pipeline usa exclusivamente algoritmos clássicos de processamento de imagem.

### 1. Conversão BGR → HSV
O OpenCV captura frames em BGR. Para análise de cor, o espaço **HSV** (Hue, Saturation, Value) é superior ao BGR porque o canal **Hue** representa a cor pura independentemente da luminosidade. Uma folha verde na sombra e uma folha verde ao sol têm o mesmo Hue, mas valores de R, G, B completamente diferentes. Isso torna a segmentação por cor muito mais robusta a variações de iluminação.

### 2. Segmentação por Faixas de Hue (`cv2.inRange`)
Três máscaras binárias são criadas com limites definidos na roda de cores HSV:
- **Verde** → Hue entre 25° e 95° — folha saudável
- **Amarelo** → Hue entre 15° e 33° — estresse hídrico ou nutricional
- **Marrom** → Hue entre 5° e 18° com baixa saturação — necrose ou doença

Cada máscara isola apenas os pixels que pertencem àquela faixa de cor.

### 3. Morfologia Matemática (`MORPH_CLOSE` + `MORPH_OPEN`)
As máscaras brutas contêm ruídos: pequenos buracos dentro da folha (`MORPH_CLOSE` os fecha) e pequenos pontos isolados fora da folha (`MORPH_OPEN` os remove). Ambas as operações usam um **elemento estruturante** (kernel) de 5×5 pixels que define a vizinhança considerada em cada operação morfológica.

### 4. Detecção de Contornos (`cv2.findContours`)
Identifica as fronteiras das regiões detectadas na máscara combinada. Contornos com área inferior a `3000 px²` são descartados para eliminar reflexos e ruídos residuais que passaram pela morfologia.

### 5. Cálculo do Índice de Saúde
```
score = (pixels_verdes / (pixels_verdes + pixels_amarelos + pixels_marrons)) × 100
```
Métrica simples e interpretável: quanto maior a proporção de verde no total foliar detectado, mais saudável está a planta.

### 6. Classificação por Limiar
| Score | Diagnóstico |
|---|---|
| ≥ 85% | Saudável |
| 60–84% | Levemente Estressada |
| 35–59% | Estressada |
| < 35% | Doente |

### 7. Visualização com `addWeighted`
Sobreposição semitransparente de cores sobre as regiões segmentadas (verde para saudável, amarelo para estresse, vermelho para doença), combinando o frame original com a camada colorida via média ponderada — preservando a textura real da folha.

---

## 🖥️ Interface

| Janela | Conteúdo |
|---|---|
| **Monitor de Saúde de Plantas** | Feed ao vivo com regiões coloridas, diagnóstico, barra de saúde e contagem de pixels |
| **Máscara** | Máscara binária com todas as regiões foliares detectadas |

---

## 📁 Estrutura do Projeto

```
plant-health-monitor/
├── main.py            # Aplicação principal
├── requirements.txt   # Dependências
└── README.md          # Documentação
```
