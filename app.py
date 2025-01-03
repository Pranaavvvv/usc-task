import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import folium
from streamlit_folium import folium_static

def load_data():
    # Read the CSV file
    try:
        df = pd.read_csv('Integrated_GPX_with_PM_Data.csv')
        return df
    except FileNotFoundError:
        st.error("Error: Could not find 'Integrated_GPX_with_PM_Data.csv'. Please make sure the file is in the same directory as this script.")
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

def main():
    st.set_page_config(page_title="Movement Pattern Analysis", layout="wide")
    st.title("Movement Pattern Analysis")

    # Load and process data
    df = load_data()
    
    if df is not None:
        # Display raw data in an expander
        with st.expander("Show Raw Data"):
            st.dataframe(df)
            
        df['Movement'] = df['Speed'].apply(get_movement_type)
        # Convert time string to datetime with European format (DD-MM-YYYY)
        df['Time'] = pd.to_datetime(df['Time'], format='%d-%m-%Y %H:%M')

        # Create tabs for different visualizations
        tab1, tab2, tab3 = st.tabs(["Movement Analysis", "Map View", "Environmental Data"])

        with tab1:
            st.subheader("Movement Patterns Over Time")
            
            # Speed vs Time plot
            fig_speed = px.line(df, x='Time', y='Speed', title='Speed Over Time')
            fig_speed.add_scatter(x=df['Time'], y=df['Speed'], mode='markers',
                                text=df['Movement'], name='Movement Type')
            st.plotly_chart(fig_speed, use_container_width=True)

            # Movement type distribution
            movement_dist = df['Movement'].value_counts()
            fig_pie = px.pie(values=movement_dist.values, names=movement_dist.index,
                            title='Distribution of Movement Types')
            st.plotly_chart(fig_pie)

            # Display movement statistics
            st.subheader("Movement Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Speed", f"{df['Speed'].mean():.3f}")
            with col2:
                st.metric("Max Speed", f"{df['Speed'].max():.3f}")
            with col3:
                st.metric("Total Distance", f"{df['Distance'].sum():.2f}")

        with tab2:
            st.subheader("Movement Map")
            
            # Create map centered on mean coordinates
            m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()],
                          zoom_start=15)

            # Add markers with movement type information
            for idx, row in df.iterrows():
                color = {
                    "Standing Still": "red",
                    "Walking": "blue",
                    "Running": "green",
                    "Driving": "purple"
                }.get(row['Movement'], "gray")
                
                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    radius=8,
                    popup=f"Time: {row['Time']}<br>Movement: {row['Movement']}<br>Speed: {row['Speed']:.3f}",
                    color=color,
                    fill=True
                ).add_to(m)

            # Draw path line
            coordinates = df[['Latitude', 'Longitude']].values.tolist()
            folium.PolyLine(
                coordinates,
                weight=2,
                color='blue',
                opacity=0.8
            ).add_to(m)

            # Add legend
            legend_html = """
                <div style="position: fixed; 
                            bottom: 50px; right: 50px; 
                            border:2px solid grey; z-index:9999; font-size:14px;
                            background-color:white;
                            padding: 10px;
                            border-radius: 5px;">
                <p><i class="fa fa-circle" style="color:red"></i> Standing Still</p>
                <p><i class="fa fa-circle" style="color:blue"></i> Walking</p>
                <p><i class="fa fa-circle" style="color:green"></i> Running</p>
                <p><i class="fa fa-circle" style="color:purple"></i> Driving</p>
                </div>
                """
            m.get_root().html.add_child(folium.Element(legend_html))

            folium_static(m)

        with tab3:
            st.subheader("Environmental Data Analysis")
            
            # PM2.5 and PM10 over time
            fig_pm = go.Figure()
            fig_pm.add_trace(go.Scatter(x=df['Time'], y=df['PM2.5'], name='PM2.5'))
            fig_pm.add_trace(go.Scatter(x=df['Time'], y=df['PM10'], name='PM10'))
            fig_pm.update_layout(title='PM2.5 and PM10 Levels Over Time')
            st.plotly_chart(fig_pm, use_container_width=True)

            # Statistics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average PM2.5", f"{df['PM2.5'].mean():.1f}")
            with col2:
                st.metric("Average PM10", f"{df['PM10'].mean():.1f}")

if __name__ == "__main__":
    main()
