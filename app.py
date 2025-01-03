import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import numpy as np
from scipy import stats

def load_data():
    try:
        df = pd.read_csv('Updated_EMA_with_PM.csv')
        return df
    except FileNotFoundError:
        st.error("Error: Could not find 'Updated_EMA_with_PM.csv'.")
        return None
    except Exception as e:
        st.error(f"Error reading the CSV file: {str(e)}")
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

def calculate_mood_metrics(df):
    df['PositiveMood'] = df[['HAPPY', 'EXCITED', 'CALM', 'RELAXED', 'PROUD']].mean(axis=1)
    df['NegativeMood'] = df[['IRRITABLE', 'ANXIOUS', 'SAD', 'BORED', 'LONELY']].mean(axis=1)
    return df

def calculate_movement_speed(df):
    df['speed'] = np.sqrt(df['LATITUDE'].diff()**2 + df['LONGITUDE'].diff()**2) / df['Time'].diff().dt.total_seconds()
    df['movement_type'] = df['speed'].apply(get_movement_type)
    return df

def calculate_weekly_stats(df, start_date):
    end_date = start_date + timedelta(days=6)
    week_mask = (df['Time'].dt.date >= start_date) & (df['Time'].dt.date <= end_date)
    week_df = df[week_mask]
    
    correlations = {}
    for pollutant in ['PM2.5_mean', 'PM10_mean']:
        for mood in ['PositiveMood', 'NegativeMood']:
            corr, p_value = stats.pearsonr(week_df[pollutant], week_df[mood])
            correlations[f"{pollutant}_{mood}"] = {'correlation': corr, 'p_value': p_value}
    
    return correlations, week_df

def main():
    st.set_page_config(page_title="Movement & Mood Analysis", layout="wide")
    st.title("Movement, Mood & Environment Analysis")

    df = load_data()
    
    if df is not None:
        df['Time'] = pd.to_datetime(df['actual_start_local'], format='%d-%m-%Y %H:%M')
        df = calculate_mood_metrics(df)
        df = calculate_movement_speed(df)
        
        view_mode = st.radio("Select View Mode", ["Daily View", "Weekly Analysis"])
        
        if view_mode == "Daily View":
            available_dates = df['Time'].dt.date.unique()
            selected_date = st.selectbox("Select Date", available_dates)
            mask = df['Time'].dt.date == selected_date
            day_df = df[mask]

            if day_df.empty:
                st.warning("No data available for selected date.")
                return

            tab1, tab2, tab3, tab4 = st.tabs(["Movement Analysis", "Combined Analysis", "Environmental Data", "Map View"])

            with tab1:
                st.subheader("Movement Pattern Analysis")
                
                # Movement pattern distribution
                movement_counts = day_df['movement_type'].value_counts()
                fig_movement = px.pie(values=movement_counts.values, 
                                    names=movement_counts.index,
                                    title='Movement Pattern Distribution')
                st.plotly_chart(fig_movement)
                
                # Movement timeline
                fig_timeline = go.Figure()
                for movement_type in day_df['movement_type'].unique():
                    mask = day_df['movement_type'] == movement_type
                    fig_timeline.add_trace(go.Scatter(
                        x=day_df[mask]['Time'],
                        y=[movement_type] * mask.sum(),
                        name=movement_type,
                        mode='markers'
                    ))
                fig_timeline.update_layout(title='Movement Timeline',
                                        yaxis_title='Movement Type',
                                        height=400)
                st.plotly_chart(fig_timeline, use_container_width=True)

            with tab2:
                st.subheader("Combined Analysis")
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=day_df['Time'], y=day_df['PositiveMood'],
                                       name='Positive Mood', yaxis='y1'))
                fig.add_trace(go.Scatter(x=day_df['Time'], y=day_df['NegativeMood'],
                                       name='Negative Mood', yaxis='y1'))
                fig.add_trace(go.Scatter(x=day_df['Time'], y=day_df['PM2.5_mean'],
                                       name='PM2.5', yaxis='y2'))
                fig.add_trace(go.Scatter(x=day_df['Time'], y=day_df['PM10_mean'],
                                       name='PM10', yaxis='y3'))

                fig.update_layout(
                    title='Combined Metrics Over Time',
                    yaxis=dict(title='Mood Score', side='left'),
                    yaxis2=dict(title='PM2.5', side='right', overlaying='y', position=0.85),
                    yaxis3=dict(title='PM10', side='right', overlaying='y', position=0.95),
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab3:
                st.subheader("Environmental Data")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Average PM2.5", f"{day_df['PM2.5_mean'].mean():.1f}")
                with col2:
                    st.metric("Average PM10", f"{day_df['PM10_mean'].mean():.1f}")

            with tab4:
                st.subheader("Movement Map")
                if 'LATITUDE' in day_df.columns and 'LONGITUDE' in day_df.columns:
                    m = folium.Map(location=[day_df['LATITUDE'].mean(), 
                                           day_df['LONGITUDE'].mean()],
                                 zoom_start=15)

                    movement_colors = {
                        "Standing Still": "blue",
                        "Walking": "green",
                        "Running": "orange",
                        "Driving": "red"
                    }

                    for idx, row in day_df.iterrows():
                        if pd.notna(row['LATITUDE']) and pd.notna(row['LONGITUDE']):
                            folium.CircleMarker(
                                location=[row['LATITUDE'], row['LONGITUDE']],
                                radius=8,
                                popup=f"""
                                Time: {row['Time']}<br>
                                Movement: {row['movement_type']}<br>
                                Positive Mood: {row['PositiveMood']:.2f}<br>
                                Negative Mood: {row['NegativeMood']:.2f}<br>
                                PM2.5: {row['PM2.5_mean']}<br>
                                PM10: {row['PM10_mean']}
                                """,
                                color=movement_colors[row['movement_type']],
                                fill=True
                            ).add_to(m)

                    folium_static(m)
                else:
                    st.warning("Location data not available for mapping.")

        else:  # Weekly Analysis
            available_weeks = pd.date_range(
                start=df['Time'].dt.date.min(),
                end=df['Time'].dt.date.max(),
                freq='W-MON'
            )
            selected_week = st.selectbox("Select Week Starting From", available_weeks)
            
            correlations, week_df = calculate_weekly_stats(df, selected_week.date())
            
            st.subheader("Weekly Pollution-Mood Correlation Analysis")
            
            # Correlation matrix heatmap
            corr_data = pd.DataFrame([
                {'Pollutant': 'PM2.5', 'Mood': 'Positive', 'Correlation': correlations['PM2.5_mean_PositiveMood']['correlation']},
                {'Pollutant': 'PM2.5', 'Mood': 'Negative', 'Correlation': correlations['PM2.5_mean_NegativeMood']['correlation']},
                {'Pollutant': 'PM10', 'Mood': 'Positive', 'Correlation': correlations['PM10_mean_PositiveMood']['correlation']},
                {'Pollutant': 'PM10', 'Mood': 'Negative', 'Correlation': correlations['PM10_mean_NegativeMood']['correlation']}
            ])
            
            fig_heatmap = px.density_heatmap(
                corr_data,
                x='Pollutant',
                y='Mood',
                z='Correlation',
                title='Pollution-Mood Correlation Matrix'
            )
            st.plotly_chart(fig_heatmap)
            
            # Weekly trends
            fig_weekly = go.Figure()
            fig_weekly.add_trace(go.Scatter(x=week_df['Time'], y=week_df['PositiveMood'],
                                          name='Positive Mood'))
            fig_weekly.add_trace(go.Scatter(x=week_df['Time'], y=week_df['NegativeMood'],
                                          name='Negative Mood'))
            fig_weekly.add_trace(go.Scatter(x=week_df['Time'], y=week_df['PM2.5_mean'],
                                          name='PM2.5'))
            fig_weekly.update_layout(title='Weekly Trends')
            st.plotly_chart(fig_weekly, use_container_width=True)
            
            # Statistical summary
            st.subheader("Statistical Summary")
            for key, value in correlations.items():
                pollutant, mood = key.split('_', 1)
                st.write(f"Correlation between {pollutant} and {mood}:")
                st.write(f"- Correlation coefficient: {value['correlation']:.3f}")
                st.write(f"- P-value: {value['p_value']:.3f}")

if __name__ == "__main__":
    main()
