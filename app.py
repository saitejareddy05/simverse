import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import random

# --- Constants & Config ---
MAX_STORY_DAYS = 365
WQ_THRESHOLDS = {
    "do": {"safe": 5.0, "critical": 2.0},  # Dissolved Oxygen (mg/L)
    "ph": {"min": 6.5, "max": 8.5},
    "nitrates": {"max": 10.0},
    "toxins": {"max": 1.0}
}

# --- Page Config ---
st.set_page_config(
    page_title="AquaGuard | Water Pollution Simulator",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS for Aesthetics ---
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: white;
    }
    .stApp {
        background-color: transparent;
    }
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .status-healthy { color: #00ff88; }
    .status-stressed { color: #ffbb00; }
    .status-critical { color: #ff4444; }
    </style>
    """, unsafe_allow_html=True)

# --- Session State Initialization ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.day = 0
    st.session_state.history = pd.DataFrame(columns=['Day', 'DO', 'pH', 'Nitrates', 'Toxins', 'Turbidity', 'Score'])
    # Initial Water Parameters
    st.session_state.params = {
        "do": 8.0,
        "ph": 7.0,
        "nitrates": 2.0,
        "toxins": 0.0,
        "turbidity": 5.0, # NTU
        "algae": 10.0,    # Index
        "plants": 100.0,  # Health %
        "score": 100,
        "eco_points": 0
    }
    st.session_state.events = []
    st.session_state.ecosystem_state = "Healthy"
    st.session_state.running = False
    st.session_state.last_weather = "Sunny"

# --- Simulation Logic ---
def update_simulation(pollution_inputs, policies):
    # pollution_inputs: dict {factory, farm, urban}
    # policies: dict {treatment, organic, regulation, cleanup}
    
    # 1. Natural Processes (Base Decay/Regeneration)
    st.session_state.params["do"] += (8.5 - st.session_state.params["do"]) * 0.15 
    st.session_state.params["nitrates"] *= 0.92
    st.session_state.params["toxins"] *= 0.85
    st.session_state.params["turbidity"] += (5.0 - st.session_state.params["turbidity"]) * 0.2
    
    # 2. Policy & Pollution Impact
    treat_mod = 0.15 if policies["treatment"] else 1.0
    org_mod = 0.35 if policies["organic"] else 1.0
    reg_mod = 0.4 if policies["regulation"] else 1.0
    cleanup_effect = 2.0 if policies["cleanup"] else 0.0
    
    # Apply Inputs
    st.session_state.params["toxins"] += (pollution_inputs["factory"] * 0.6 * treat_mod * reg_mod)
    st.session_state.params["nitrates"] += (pollution_inputs["farm"] * 0.9 * org_mod)
    st.session_state.params["turbidity"] += (pollution_inputs["urban"] * 1.5) + (pollution_inputs["factory"] * 0.4 * treat_mod)
    st.session_state.params["do"] -= (pollution_inputs["urban"] * 0.4) 
    
    # Secondary Effects
    # Algae growth depends on nitrates
    algae_growth = (st.session_state.params["nitrates"] * 0.5) - (st.session_state.params["turbidity"] * 0.1)
    st.session_state.params["algae"] = max(0, min(100, st.session_state.params["algae"] + algae_growth))
    
    # High algae depletes DO at night (simulated as overall depletion when very high)
    if st.session_state.params["algae"] > 40:
        st.session_state.params["do"] -= (st.session_state.params["algae"] - 40) * 0.05
    
    # Plants suffer from toxins and high turbidity (no light)
    plant_damage = (st.session_state.params["toxins"] * 2.0) + (max(0, st.session_state.params["turbidity"] - 20) * 0.5)
    st.session_state.params["plants"] = max(0, min(100, st.session_state.params["plants"] - plant_damage + 2))
    
    # Cleanup drive helps reduce toxins and turbidity
    st.session_state.params["toxins"] = max(0, st.session_state.params["toxins"] - cleanup_effect * 0.5)
    st.session_state.params["turbidity"] = max(5, st.session_state.params["turbidity"] - cleanup_effect * 2)

    # Bound Parameters
    st.session_state.params["do"] = max(0, min(12, st.session_state.params["do"]))
    st.session_state.params["ph"] = 7.0 + (st.session_state.params["toxins"] * -0.25) + (st.session_state.params["nitrates"] * 0.15)
    st.session_state.params["ph"] = max(1, min(14, st.session_state.params["ph"]))

    # 3. Ecosystem Health State
    if st.session_state.params["do"] < 2.5 or st.session_state.params["toxins"] > 4.5 or st.session_state.params["plants"] < 20:
        st.session_state.ecosystem_state = "Critical"
    elif st.session_state.params["do"] < 4.5 or st.session_state.params["nitrates"] > 7.5 or st.session_state.params["turbidity"] > 30:
        st.session_state.ecosystem_state = "Stressed"
    else:
        st.session_state.ecosystem_state = "Healthy"
        
    # 4. Score & Eco-Points
    daily_points = 0
    if st.session_state.ecosystem_state == "Healthy":
        daily_points = 10
        penalties = -2
    elif st.session_state.ecosystem_state == "Stressed":
        daily_points = 2
        penalties = 5
    else:
        daily_points = 0
        penalties = 15
        
    st.session_state.params["eco_points"] += daily_points
    st.session_state.params["score"] = max(0, min(100, st.session_state.params["score"] - penalties))

    # 5. Save History
    new_row = {
        'Day': st.session_state.day,
        'DO': st.session_state.params["do"],
        'pH': st.session_state.params["ph"],
        'Nitrates': st.session_state.params["nitrates"],
        'Toxins': st.session_state.params["toxins"],
        'Turbidity': st.session_state.params["turbidity"],
        'Score': st.session_state.params["score"]
    }
    st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([new_row])], ignore_index=True)
    
    # 6. Random Weather Event
    st.session_state.last_weather = trigger_weather()
    st.session_state.day += 1

# --- Badge System ---
def render_badges():
    st.sidebar.markdown("---")
    st.sidebar.header("🏆 Achievements")
    if st.session_state.params["score"] > 90 and st.session_state.day > 10:
        st.sidebar.success("🍃 Guardian of the Stream")
    if st.session_state.day > 30:
        st.sidebar.info("🕰️ Long-Term Manager")
    if st.session_state.params["do"] > 7 and st.session_state.params["toxins"] < 0.5:
        st.sidebar.warning("✨ Crystal Clear")
def render_header():
    st.title("🛡️ AquaGuard: River Ecosystem Manager")
    st.markdown("Monitor and control water pollution to protect aquatic life. Balance industrial growth with environmental health.")

def render_sidebar():
    st.sidebar.header("🏭 Pollution Sources")
    factory = st.sidebar.slider("Industrial Output", 0.0, 10.0, 2.0, help="Releases Toxins and increases Turbidity.")
    farm = st.sidebar.slider("Agricultural Activity", 0.0, 10.0, 2.0, help="Chief source of Nitrates (Fertilizers).")
    urban = st.sidebar.slider("Urban Expansion", 0.0, 10.0, 1.0, help="Increases Turbidity and depletes Oxygen.")
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚖️ Interventions")
    treatment = st.sidebar.checkbox("Wastewater Treatment Plant", help="Reduces factory toxic output.")
    organic = st.sidebar.checkbox("Organic Farming Subsidies", help="Reduces nitrate runoff from farms.")
    regulation = st.sidebar.checkbox("State Emission Regulations", help="Strict caps on all industrial waste.")
    cleanup = st.sidebar.checkbox("Active Cleanup Drive", help="Volunteers removing plastics and surface waste.")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Simulate Next Day ⏩", use_container_width=True):
        update_simulation(
            {"factory": factory, "farm": farm, "urban": urban},
            {"treatment": treatment, "organic": organic, "regulation": regulation, "cleanup": cleanup}
        )
    
    if st.sidebar.button("Reset Simulation 🔄", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    return {"factory": factory, "farm": farm, "urban": urban}, {"treatment": treatment, "organic": organic, "regulation": regulation, "cleanup": cleanup}

def render_dashboard():
    # Show Eco-Points in a special header
    st.markdown(f"### 🎖️ Eco-Points: {st.session_state.params['eco_points']} | Day {st.session_state.day}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""<div class='metric-card'>
            <h4>Dissolved Oxygen</h4>
            <h2 class='{ "status-healthy" if st.session_state.params["do"] > 5 else "status-stressed" if st.session_state.params["do"] > 2.5 else "status-critical" }'>
                {st.session_state.params["do"]:.2f} mg/L
            </h2>
        </div>""", unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""<div class='metric-card'>
            <h4>Turbidity</h4>
            <h2 class='{ "status-healthy" if st.session_state.params["turbidity"] < 15 else "status-stressed" if st.session_state.params["turbidity"] < 40 else "status-critical" }'>
                {st.session_state.params["turbidity"]:.1f} NTU
            </h2>
        </div>""", unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""<div class='metric-card'>
            <h4>Ecosystem Health</h4>
            <h2 class='{ "status-healthy" if st.session_state.ecosystem_state == "Healthy" else "status-stressed" if st.session_state.ecosystem_state == "Stressed" else "status-critical" }'>
                {st.session_state.ecosystem_state}
            </h2>
        </div>""", unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""<div class='metric-card'>
            <h4>Sustainability Score</h4>
            <h2>{st.session_state.params["score"]:.0f}%</h2>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # Secondary Parameters
    c1, c2, c3 = st.columns(3)
    c1.metric("Nitrates", f"{st.session_state.params['nitrates']:.2f} mg/L", delta_color="inverse")
    c2.metric("Algae Growth", f"{st.session_state.params['algae']:.1f}%")
    c3.metric("Plant Life", f"{st.session_state.params['plants']:.1f}%")

    # Charting and Comparison
    tab1, tab2 = st.tabs(["📊 Trends", "📉 Before vs After"])
    
    with tab1:
        if not st.session_state.history.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=st.session_state.history['Day'], y=st.session_state.history['DO'], name="Oxygen (DO)", line=dict(color='#00ff88')))
            fig.add_trace(go.Scatter(x=st.session_state.history['Day'], y=st.session_state.history['Nitrates'], name="Nitrates", line=dict(color='#ffbb00')))
            fig.add_trace(go.Scatter(x=st.session_state.history['Day'], y=st.session_state.history['Toxins'], name="Toxins", line=dict(color='#ff4444')))
            fig.add_trace(go.Scatter(x=st.session_state.history['Day'], y=st.session_state.history['Turbidity'], name="Turbidity", line=dict(color='#795548')))
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis_title="Day",
                yaxis_title="Levels"
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if len(st.session_state.history) > 1:
            initial = st.session_state.history.iloc[0]
            current = st.session_state.history.iloc[-1]
            
            comp_data = pd.DataFrame({
                "Parameter": ["DO", "Nitrates", "Toxins", "Turbidity", "Score"],
                "Initial": [initial["DO"], initial["Nitrates"], initial["Toxins"], initial["Turbidity"], initial["Score"]],
                "Current": [current["DO"], current["Nitrates"], current["Toxins"], current["Turbidity"], current["Score"]]
            })
            
            fig_comp = go.Figure(data=[
                go.Bar(name='Initial State (Day 0)', x=comp_data["Parameter"], y=comp_data["Initial"], marker_color='#00b0ff'),
                go.Bar(name='Current State', x=comp_data["Parameter"], y=comp_data["Current"], marker_color='#ffbb00')
            ])
            fig_comp.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Simulation history needed for comparison. Advance at least 1 day.")

# --- Visual Ecosystem Helper ---
def get_river_color():
    # Blend colors based on status
    nitrates = st.session_state.params["nitrates"]
    toxins = st.session_state.params["toxins"]
    turbidity = st.session_state.params["turbidity"]
    
    if toxins > 3.0: return "#5d4037" # Dirty brown
    if nitrates > 8.0: return "#2e7d32" # Algal green
    if turbidity > 30: return "#795548" # Silt brown
    return "#00b0ff" # Healthy blue

def render_river():
    color = get_river_color()
    state = st.session_state.ecosystem_state
    
    # Icons based on health
    fish_count = int(max(0, st.session_state.params["do"] - 3))
    algae_icons = "🌿" * int(st.session_state.params["algae"] / 20)
    plant_icons = "🌱" * int(st.session_state.params["plants"] / 20)
    fish_icons = "🐟" * fish_count
    
    st.markdown(f"""
    <div style="background: {color}; height: 200px; border-radius: 20px; transition: background 2s; 
                display: flex; flex-direction: column; justify-content: center; align-items: center; 
                border: 4px solid rgba(255,255,255,0.2); margin-bottom: 20px; position: relative; overflow: hidden;">
        <div style="position: absolute; bottom: 10px; left: 20px; font-size: 2rem;">{plant_icons}</div>
        <div style="position: absolute; top: 10px; right: 20px; font-size: 1.5rem;">{algae_icons}</div>
        <h3 style="color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); z-index: 10;">{state} Ecosystem</h3>
        <div style="font-size: 2.5rem; animation: float 3s ease-in-out infinite;">
            {fish_icons if fish_count > 0 else "💀"}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Weather Logic ---
def trigger_weather():
    events = ["Sunny", "Heavy Rain", "Drought", "Flash Flood"]
    event = random.choices(events, weights=[0.7, 0.1, 0.1, 0.1])[0]
    
    if event == "Heavy Rain":
        st.session_state.params["nitrates"] += 2.0 # Runoff
        st.info("🌧️ Heavy Rain Alert: Nutrient runoff has increased!")
    elif event == "Drought":
        st.session_state.params["toxins"] *= 1.2 # Concentration increase
        st.session_state.params["do"] -= 1.0
        st.warning("☀️ Drought Alert: Water levels low, pollutants concentrating!")
    elif event == "Flash Flood":
        st.session_state.params["do"] += 1.0 # Aeration but waste wash-in
        st.session_state.params["toxins"] += 1.0
        st.error("🌊 Flash Flood! Waste tanks overflowed, but water is aerated.")
    
    return event

# --- Updated Main App ---
def main():
    render_header()
    inputs, policies = render_sidebar()
    
    # Simulation Logic Update with Weather
    if 'last_weather' not in st.session_state:
        st.session_state.last_weather = "Sunny"

    render_river()
    render_dashboard()
    render_badges()
    
    # AI Recommendation
    with st.expander("🤖 AquaAI Advisor", expanded=True):
        if st.session_state.params["do"] < 4:
            st.warning("🚨 Critical Oxygen Levels! Industrial or urban waste is depleting the river's breath. Consider Wastewater Treatment or Emission Regulations.")
        elif st.session_state.params["nitrates"] > 7.5:
            st.info("🌿 Algal Bloom Imminent! High nitrates from farm runoff detected. Enable Organic Farming Subsidies.")
        elif st.session_state.params["toxins"] > 3.5:
            st.error("☠️ Toxic Contamination! Factory leakage is reaching lethal levels. Regulation and Cleanup Drive are urgent.")
        elif st.session_state.params["turbidity"] > 35:
            st.warning("🟤 High Turbidity! Silt and urban debris are blocking sunlight, killing plants. Start a Cleanup Drive.")
        else:
            st.success("✨ The river is thriving. Your management is maintaining a healthy balance.")

    # Show active weather
    st.sidebar.markdown(f"**Current Weather:** {st.session_state.last_weather}")
    st.sidebar.markdown(f"**Timeline:** Month {int(st.session_state.day/30) + 1} | Day {st.session_state.day % 30}")

if __name__ == "__main__":
    main()
