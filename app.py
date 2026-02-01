import streamlit as st
import math
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# --- PAGE CONFIG ---
st.set_page_config(page_title="BioFloc Master Pro", layout="wide")

# --- DATABASE FILES ---
DB_FILE = "biofloc_research_v7.csv" 
MORT_FILE = "mortality_v7.csv"
EXP_FILE = "finance_v7.csv"

def save_data(data, filename):
    df_new = pd.DataFrame([data])
    if not os.path.isfile(filename):
        df_new.to_csv(filename, index=False, encoding='utf-8-sig')
    else:
        pd.concat([pd.read_csv(filename), df_new], ignore_index=True).to_csv(filename, index=False, encoding='utf-8-sig')

# --- SIDEBAR & LOGO ---
if os.path.exists("logo.png"):
    st.sidebar.image(Image.open("logo.png"), use_container_width=True)

st.sidebar.header("📐 Research Setup")
pond_id = st.sidebar.text_input("Tank ID", "Exp-01")
volume = st.sidebar.number_input("Water Volume (m³)", value=15.0, min_value=None)
initial_density = st.sidebar.number_input("Stocking Density (Fish/m³)", value=100.0, min_value=None)

# Mortality & Population Logic
total_dead = 0
if os.path.isfile(MORT_FILE):
    m_df = pd.read_csv(MORT_FILE)
    total_dead = m_df[m_df["Pond_ID"] == pond_id]["Dead_Count"].sum()
initial_count = int(volume * initial_density)
current_count = initial_count - total_dead

st.sidebar.divider()
st.sidebar.metric("Live Fish Population", f"{current_count}")
st.sidebar.metric("Current Density", f"{round(current_count/volume, 2)} Fish/m³")

# --- MAIN INTERFACE ---
st.title("🛡️ BioFloc Expert v7.0: Total Nitrogen & Research Edition")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Daily Entry", "📈 Analytics & Growth", "💰 Financials", "⚙️ Edit/Delete", "📂 Export"])

# --- TAB 1: ENTRY (Open Ranges) ---
with tab1:
    st.subheader("Daily Parameter Logging")
    with st.form("entry_form"):
        date_in = st.date_input("Entry Date", datetime.now())
        c1, c2, c3 = st.columns(3)
        
        # All inputs are unrestricted (min_value=None)
        temp = c1.number_input("Temp (°C)", value=28.0, min_value=None)
        do = c1.number_input("Oxygen (mg/L)", value=5.5, min_value=None)
        tan = c1.number_input("Ammonia (TAN mg/L)", value=0.1, min_value=None)
        nitrite = c1.number_input("Nitrite (NO2 mg/L)", value=0.01, min_value=None)
        
        ph = c2.number_input("pH", value=7.5, min_value=None)
        alk = c2.number_input("Alkalinity (mg/L)", value=120.0, min_value=None)
        nitrate = c2.number_input("Nitrate (NO3 mg/L)", value=10.0, min_value=None)
        f_vol = c2.number_input("Floc Volume (ml/L)", value=25.0, min_value=None)
        
        w_g = c3.number_input("Avg Fish Weight (g)", value=50.0, min_value=None)
        f_rate = c3.number_input("Feed Rate (% of Biomass)", value=2.0, min_value=None)
        prot = st.slider("Feed Protein (%)", 10, 50, 30)
        
        if st.form_submit_button("Submit Daily Data"):
            # CALCULATIONS
            biomass = (current_count * w_g) / 1000
            feed = biomass * (f_rate / 100)
            molasses = (feed * (prot/100) * 0.16 * 15) / 0.4
            
            # Total Nitrogen Calculation (Estimated: TAN + Nitrite + Nitrate)
            total_n = tan + nitrite + nitrate
            
            save_data({
                "Date": date_in.strftime("%Y-%m-%d"), "Pond": pond_id, "Temp": temp, "DO": do, 
                "pH": ph, "Alk": alk, "TAN": tan, "NO2": nitrite, "NO3": nitrate, "Total_N": total_n,
                "Floc": f_vol, "Weight": w_g, "Biomass_kg": round(biomass, 2), 
                "Feed_kg": round(feed, 2), "Molasses_kg": round(molasses, 2)
            }, DB_FILE)
            st.success(f"Data for {date_in} has been successfully recorded.")

# --- TAB 2: ANALYTICS (Graphs) ---
with tab2:
    if os.path.isfile(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            
            st.write("### 📈 Biological Performance (Weight & Biomass)")
            st.line_chart(df.set_index('Date')[['Weight', 'Biomass_kg']])
            
            st.write("### 🧪 Nitrogen Cycle Dynamics (TAN, NO2, NO3, Total N)")
            st.line_chart(df.set_index('Date')[['TAN', 'NO2', 'NO3', 'Total_N']])
            
            st.write("### 🌫️ Floc Volume vs Alkalinity")
            st.line_chart(df.set_index('Date')[['Floc', 'Alk']])
            
            if len(df) > 1:
                sgr = (math.log(df['Weight'].iloc[-1]) - math.log(df['Weight'].iloc[-2])) * 100
                st.metric("SGR (Growth Rate)", f"{round(sgr, 2)} %/day")
        else:
            st.info("No data entries to visualize.")

# --- TAB 3: FINANCE ---
with tab3:
    with st.form("fin"):
        d_exp = st.date_input("Expense Date", datetime.now())
        cat = st.selectbox("Category", ["Feed", "Power", "Labor", "Molasses", "Seed", "Misc"])
        amt = st.number_input("Cost Amount", min_value=None)
        if st.form_submit_button("Log Expense"):
            save_data({"Date": d_exp.strftime("%Y-%m-%d"), "Category": cat, "Cost": amt}, EXP_FILE)

# --- TAB 4: EDIT / DELETE ---
with tab4:
    st.subheader("🛠️ Database Correction")
    if os.path.isfile(DB_FILE):
        edit_df = pd.read_csv(DB_FILE)
        dates_to_del = st.multiselect("Select dates to delete records:", options=edit_df['Date'].unique())
        if st.button("Confirm Delete"):
            edit_df = edit_df[~edit_df['Date'].isin(dates_to_del)]
            edit_df.to_csv(DB_FILE, index=False)
            st.rerun()

# --- TAB 5: EXPORT & MORTALITY ---
with tab5:
    if os.path.isfile(DB_FILE):
        st.write("### Raw Research Data")
        st.dataframe(pd.read_csv(DB_FILE).sort_values('Date', ascending=False))
        st.download_button("📥 Download Database (CSV)", pd.read_csv(DB_FILE).to_csv(), "biofloc_v7_data.csv")
    
    st.divider()
    with st.form("mort"):
        st.subheader("💀 Report Fish Mortality")
        m_num = st.number_input("Number of fish lost", step=1, value=0)
        if st.form_submit_button("Record Mortality"):
            save_data({"Date": datetime.now().strftime("%Y-%m-%d"), "Pond_ID": pond_id, "Dead_Count": m_num}, MORT_FILE)
            st.rerun()
