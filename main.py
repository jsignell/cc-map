# This script reads a list of addresses from a CSV, geocodes them,
# and creates a static map using matplotlib and cartopy.

import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from pathlib import Path
import time

INPUT_FILE = "data.csv"
GEOCODED_FILE = "geocoded.csv"

def geocode_address(address, geolocator):
    """
    Attempts to geocode a single address with retry logic.
    Returns a tuple of (latitude, longitude) or (None, None) on failure.
    """
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return (location.latitude, location.longitude)
        else:
            print(f"Could not find coordinates for: {address}")
            return (None, None)
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding service error for '{address}': {e}. Retrying...")
        time.sleep(2)  # Wait and retry
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                return (location.latitude, location.longitude)
        except (GeocoderTimedOut, GeocoderServiceError):
            print(f"Failed again for '{address}'. Skipping.")
            return (None, None)
    return (None, None)


def do_geocoding():
    # --- 1. Read CSV file from data.csv ---
    df = pd.read_csv(INPUT_FILE)
    df["full_address"] = df["address"] + ', ' + df["city"] + ", " + df["state_abbr"] + " " + df["zip"]

    # --- 2. Geocode the addresses ---
    print("Geocoding addresses...")
    geolocator = Nominatim(user_agent="address_mapper")
    
    # Apply the geocoding function to each address in the DataFrame
    df[['latitude', 'longitude']] = df['full_address'].apply(
        lambda x: pd.Series(geocode_address(x, geolocator))
    )

    # Save it out to a file for later use
    df.to_csv(GEOCODED_FILE, index=False)

    # Filter out rows where geocoding failed
    df_valid = df.dropna(subset=['latitude', 'longitude']).reset_index(drop=True)

    if len(df_valid) != len(df):

        raise ValueError(
            f"Successfully geocoded {len(df_valid)} out of {len(df)} addresses."
            f"Failed on {df[df.isna(subset=['latitude', 'longitude'])]}"
        )


def create_map_from_csv():
    """
    Main function to read addresses from a CSV, geocode, and plot them on a map.
    """
    # See if the data has already been geocoded
    if not Path(GEOCODED_FILE).exists():
        do_geocoding()

    # Read in geocoded data
    df = pd.read_csv(GEOCODED_FILE)
    
    if df.empty:
        print("No valid addresses to plot. Exiting.")
        return

    # --- 3. Create the map using Cartopy and Matplotlib ---
    fig = plt.figure(figsize=(10, 8))
    # Use PlateCarree projection for a simple, rectangular map
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    # Add map features for context and aesthetic appeal
    ax.set_title('Massachusetts Community Colleges', fontsize=16)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.STATES, linestyle='-', edgecolor='gray')
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    # Make the ocean blue and stuff
    # ax.add_feature(cfeature.OCEAN, color='#ADD8E6')
    # ax.add_feature(cfeature.LAND, color='#F5F5DC')
    # ax.add_feature(cfeature.LAKES, color='#ADD8E6')
    # ax.add_feature(cfeature.RIVERS)

    # Plot the geocoded points

    # A list of colors for each point
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'cyan', 'magenta', 'lime',
              'brown', 'pink', 'gray', 'olive', 'teal', 'navy', 'maroon', 'gold']

    # Plot each point individually with a different color and label for the legend
    for index, row in df.iterrows():
        # Use modulo to cycle through colors if there are more addresses than colors
        color = colors[index]
        ax.scatter(row['longitude'], row['latitude'],
                   transform=ccrs.PlateCarree(),
                   color=color, marker='o', s=70,
                   label=row['inst_name'])


    # Add labels to the points (optional)
    # for index, row in df.iterrows():
    #     ax.text(row['longitude'] + 0.5, row['latitude'], row['address'].split(',')[0],
    #             transform=ccrs.PlateCarree(), fontsize=8, ha='left')

    # Set the map extent to fit all the points with a buffer
    min_lon, max_lon = df['longitude'].min(), df['longitude'].max()
    min_lat, max_lat = df['latitude'].min(), df['latitude'].max()
    buffer = 1.5 # Degrees buffer
    ax.set_extent([min_lon - .3, max_lon + .5, min_lat - 1.7, max_lat + 0.3],
                  crs=ccrs.PlateCarree())

       # Create the legend and place it at the bottom right
    ax.legend(loc='lower left', ncol=2)
    fig.savefig('address_map.png', dpi=300)
    print("Map saved as 'address_map.png'")

# Execute the function
if __name__ == "__main__":
    create_map_from_csv()

