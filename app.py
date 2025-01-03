import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import folium
from geopy.distance import geodesic

# Function to load data
def load_data():
    # Load the specific file
    file_path = 'Integrated_GPX_with_PM_Data.csv'
    return pd.read_csv(file_path)

# Classify movement based on speed
def classify_movement(speed):
    if speed == 0:
        return "Still"
    elif speed < 1.5:
        return "Walking"
    elif speed < 10:
        return "Running"
    else:
        return "Driving"

# Process data to add movement classification
def process_data(df):
    df['Movement'] = df['Speed'].apply(classify_movement)
    return df

# Plot movement patterns on a graph
def plot_movement(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot lat, long as a path
    ax.plot(df['Longitude'], df['Latitude'], marker='o', linestyle='-', color='b', label='Path')

    # Color code based on movement type
    for idx, row in df.iterrows():
        if row['Movement'] == 'Still':
            ax.scatter(row['Longitude'], row['Latitude'], color='red', label='Still')
        elif row['Movement'] == 'Walking':
            ax.scatter(row['Longitude'], row['Latitude'], color='green', label='Walking')
        elif row['Movement'] == 'Running':
            ax.scatter(row['Longitude'], row['Latitude'], color='orange', label='Running')
        else:
            ax.scatter(row['Longitude'], row['Latitude'], color='purple', label='Driving')

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Participants Movement Patterns')

    # Show unique legend
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[:4], labels[:4])

    return fig

# Plot movement on an interactive map using folium
def plot_on_map(df):
    m = folium.Map(location=[df['Latitude'].iloc[0], df['Longitude'].iloc[0]], zoom_start=15)

    # Plot each movement point
    for idx, row in df.iterrows():
        color = "red" if row['Movement'] == "Still" else "green" if row['Movement'] == "Walking" else "orange" if row['Movement'] == "Running" else "purple"
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6
        ).add_to(m)

    return m

# Streamlit app layout
def app():
    st.title("Movement Pattern Display")

    # Button to trigger file processing for Integrated_GPX_with_PM_Data.csv
    if st.button("Load Integrated_GPX_with_PM_Data.csv"):
        # Load and process data
        try:
            df = load_data()

            # Check if required columns exist
            required_columns = ['Latitude', 'Longitude', 'Speed', 'Time', 'Distance']
            if not all(col in df.columns for col in required_columns):
                st.error("CSV file must contain the following columns: Latitude, Longitude, Speed, Time, Distance.")
                return

            # Process data to add movement classifications
            df = process_data(df)

            # Show data preview
            st.write("Data Preview", df.head())

            # Movement Type Filter
            movement_filter = st.selectbox("Filter by Movement Type", ["All", "Still", "Walking", "Running", "Driving"])

            # Filter data based on selected movement type
            if movement_filter != "All":
                df = df[df['Movement'] == movement_filter]

            # Display a button to download the processed data as CSV
            st.download_button(
                label="Download Processed Data",
                data=df.to_csv(index=False),
                file_name="processed_movement_data.csv",
                mime="text/csv"
            )

            # Display a map with movement points
            st.subheader("Movement Pattern on Map")
            map_object = plot_on_map(df)
            st.write(map_object)

            # Display the movement graph
            st.subheader("Movement Pattern Graph")
            fig = plot_movement(df)
            st.pyplot(fig)
        except FileNotFoundError:
            st.error("The file 'Integrated_GPX_with_PM_Data.csv' was not found in the directory.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    app()
