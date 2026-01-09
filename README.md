# 🌊 AquaGuard: River Ecosystem Simulator

AquaGuard is an interactive, web-based simulation tool built with Python and Streamlit. It is designed to educate users on the complex cause-and-effect relationships within water ecosystems, allowing them to act as environmental managers.

## 🚀 Overview

The simulator models a virtual river ecosystem where industrial, agricultural, and urban activities impact water quality. Users must balance economic growth with environmental sustainability by adjusting pollution sources and enacting mitigation policies.

## ✨ Features

- **Dynamic Simulation Engine**: Realistic rule-based logic governing:
  - **Dissolved Oxygen (DO)**: Vital for fish survival; depleted by organic waste and algal blooms.
  - **Nitrates**: Driven by agricultural fertilizers; leads to eutrophication (algal blooms).
  - **Toxins**: Chemical waste from factories that harms plants and aquatic life.
  - **Turbidity**: Silt and debris that block sunlight and damage habitats.
  - **pH Balance**: Vital for chemical stability in the water.
- **Interactive Visual Ecosystem**:
  - The river color changes dynamically (Blue → Green → Brown).
  - Fish populations and plant life icons reflect the current health state.
- **Policy Interventions**:
  - Wastewater Treatment Plants
  - Organic Farming Subsidies
  - Emission Regulations
  - Active Cleanup Drives
- **Advanced Analytics**:
  - Real-time Plotly charts for parameter tracking.
  - "Before vs After" comparison tool to visualize long-term impact.
- **Gamification**:
  - **Eco-Points**: Earn points for maintaining a healthy ecosystem.
  - **Sustainability Score**: A 0-100% metric of your management success.
  - **Achievement Badges**: Unlock rewards like "Guardian of the Stream".

## 🛠️ Tech Stack

- **Backend/Frontend**: [Streamlit](https://streamlit.io/) (Python)
- **Data Visualization**: [Plotly](https://plotly.com/python/) & [Pandas](https://pandas.pydata.org/)
- **Simulation**: Custom rule-based mathematical model.

## 🏃 Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone [<repository-url>](https://github.com/saitejareddy05/simverse)
   cd simverse
   ```

2. Install dependencies:
   ```bash
   pip install streamlit pandas plotly numpy
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## 🎮 How to Play

1.  **Observe**: Check the initial "Healthy" state of the river.
2.  **Adjust**: Use the sliders in the sidebar to increase factory output or urban sprawl.
3.  **Simulate**: Click "Simulate Next Day" to see how your changes affect the metrics.
4.  **React**: When parameters enter "Stressed" or "Critical" zones (follow the **AquaAI Advisor**), enable policies to mitigate the damage.
5.  **Achieve**: Aim for a 100% Sustainability Score and collect all badges.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
