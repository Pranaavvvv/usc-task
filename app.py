import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import folium
from streamlit_folium import folium_static

def load_data():
    try:
        df = pd.read_csv('Integrated_GPX_with_PM_Data.csv')
        return df
    except FileNotFoundError:
        st.error("Error: Could not find 'Integrated_GPX_with_PM_Data.csv'.")
        return None
    except Exception as e:
        st.error(f"Error reading the CSV file: {str(e)}")
        return None

def load_ema_data():
    try:
        ema_df = pd.read_csv('Updated_EMA_with_PM.csv')
        st.write("Columns in EMA dataset:", ema_df.columns)
        
        # Assuming 'actual_start_local' is the timestamp column
        if 'actual_start_local' not in ema_df.columns:
            st.error("The 'actual_start_local' column is missing in the EMA dataset.")
            return None
        
        # Convert to datetime
        ema_df['actual_start_local'] = pd.to_datetime(ema_df['actual_start_local'], errors='coerce')
        
        if ema_df['actual_start_local'].isnull().any():
            st.warning("Some rows have invalid timestamps in 'actual_start_local' and were coerced to NaT.")
        
        return ema_df
    except FileNotFoundError:
        st.error("Error: Could not find 'Updated_EMA_with_PM.csv'.")
        return None
    except Exception as e:
        st.error(f"Error reading the EMA CSV file: {str(e)}")
        return None

def get_movement_type(speed):
    if speed < 0.05:
        return "Standing Still"
    elif speed < 0.3:
        return "Walking"
    elif speed < 1:
        return "Running"
    else:
        return "Driving"

def main():
    st.set_page_config(page_title="Movement Pattern Analysis", layout="wide")
    st.title("Movement Pattern Analysis")

    # Load and process data
    df = load_data()
    ema_df = load_ema_data()
    
    if df is not None:
        # Convert time string to datetime with European format (DD-MM-YYYY)
        df['Time'] = pd.to_datetime(df['Time'], format='%d-%m-%Y %H:%M')
        df['Movement'] = df['Speed'].apply(get_movement_type)
        
        # Date selection
        available_dates = df['Time'].dt.date.unique()
        selected_date = st.selectbox("Select Date", available_dates)
        
        # Filter data for selected date
        mask = df['Time'].dt.date == selected_date
        day_df = df[mask]

        if day_df.empty:
            st.warning("No data available for selected date.")
            return

        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Combined Analysis", 
            "Movement Analysis", 
            "Map View", 
            "Environmental Data", 
            "Weekly Analytics"
        ])

        with tab1:
            st.subheader("Combined Movement, Pollution, and Mood Analysis")
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=day_df['Time'],
                y=day_df['Speed'],
                name='Speed',
                yaxis='y1'
            ))
            
            fig.add_trace(go.Scatter(
                x=day_df['Time'],
                y=day_df['PM2.5'],
                name='PM2.5',
                yaxis='y2'
            ))
            
            fig.add_trace(go.Scatter(
                x=day_df['Time'],
                y=day_df['PM10'],
                name='PM10',
                yaxis='y3'
            ))

            fig.update_layout(
                title='Combined Analysis Over Time',
                yaxis=dict(title='Speed', side='left'),
                yaxis2=dict(title='PM2.5', side='right', overlaying='y', position=0.85),
                yaxis3=dict(title='PM10', side='right', overlaying='y', position=0.95),
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Movement Patterns")
            
            fig_speed = px.line(day_df, x='Time', y='Speed', title='Speed Over Time')
            fig_speed.add_scatter(x=day_df['Time'], y=day_df['Speed'], 
                                mode='markers', text=day_df['Movement'], 
                                name='Movement Type')
            st.plotly_chart(fig_speed, use_container_width=True)

            movement_dist = day_df['Movement'].value_counts()
            fig_pie = px.pie(values=movement_dist.values, names=movement_dist.index,
                            title='Distribution of Movement Types')
            st.plotly_chart(fig_pie)

            st.subheader("Movement Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Speed", f"{day_df['Speed'].mean():.3f}")
            with col2:
                st.metric("Max Speed", f"{day_df['Speed'].max():.3f}")
            with col3:
                st.metric("Total Distance", f"{day_df['Distance'].sum():.2f}")

        with tab3:
            st.subheader("Movement Map")
            
            m = folium.Map(location=[day_df['Latitude'].mean(), 
                                   day_df['Longitude'].mean()],
                          zoom_start=15)

            for idx, row in day_df.iterrows():
                color = {
                    "Standing Still": "red",
                    "Walking": "blue",
                    "Running": "green",
                    "Driving": "purple"
                }.get(row['Movement'], "gray")
                
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=8,
                    popup=f"""
                    Time: {row['Time']}<br>
                    Movement: {row['Movement']}<br>
                    Speed: {row['Speed']:.3f}<br>
                    PM2.5: {row['PM2.5']}<br>
                    PM10: {row['PM10']}
                    """,
                    color=color,
                    fill=True
                ).add_to(m)

            coordinates = day_df[['Latitude', 'Longitude']].values.tolist()
            folium.PolyLine(coordinates, weight=2, color='blue', opacity=0.8).add_to(m)

            folium_static(m)

        with tab4:
            st.subheader("Environmental Data Analysis")
            
            fig_pm = go.Figure()
            fig_pm.add_trace(go.Scatter(x=day_df['Time'], y=day_df['PM2.5'], 
                                      name='PM2.5'))
            fig_pm.add_trace(go.Scatter(x=day_df['Time'], y=day_df['PM10'], 
                                      name='PM10'))
            fig_pm.update_layout(title='PM2.5 and PM10 Levels Over Time')
            st.plotly_chart(fig_pm, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average PM2.5", f"{day_df['PM2.5'].mean():.1f}")
            with col2:
                st.metric("Average PM10", f"{day_df['PM10'].mean():.1f}")

        with tab5:
            st.subheader("Weekly Analytics")
            
            if ema_df is not None:
                ema_df['Week'] = ema_df['actual_start_local'].dt.isocalendar().week
                weekly_avg = ema_df.groupby('Week').mean()[['HAPPY', 'PM2.5_mean', 'PM10_mean']]
                fig_weekly = px.line(weekly_avg, x=weekly_avg.index, y=['HAPPY', 'PM2.5_mean', 'PM10_mean'], 
                                     labels={'value': 'Metric', 'Week': 'Week'},
                                     title='Weekly Analysis of Mood and Pollution')
                st.plotly_chart(fig_weekly, use_container_width=True)

if __name__ == "__main__":
    main()
