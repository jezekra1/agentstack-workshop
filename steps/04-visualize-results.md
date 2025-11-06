# Visualize flight details

## Step 1: install dependencies

We will use `airportsdata` to find location data for airport codes, the `folium` library for generating interactive map
for the resulting flight routes and also `matplotlib` for creating a static PNG. Before we start, install the required
dependencies:

```bash
uv add airportsdata \
    folium \
    geopandas \
    mapclassify \
    matplotlib \
    openinference-instrumentation-beeai \
    pyyaml \
    shapely
```

## Step 2: Create visualization functions

Here are visualization functions you can use to produce the desired outputs.

> Pro TIP: use your favorite coding assistant to generate these!

We will save these to a file `src/agentstack_agents/visualize.py`:

<details>
  <summary>Visualization functions</summary>

```python
import airportsdata
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors
from shapely.geometry import Point, LineString
from io import BytesIO


def prepare_flight_data(flights):
    """Prepare GeoDataFrames for flights and airports with waypoint support"""

    airports = airportsdata.load("IATA")

    # Generate colors from matplotlib colormap (you can change 'tab10' to 'Set1', 'Set2', 'Set3', 'Paired', etc.)
    cmap = plt.cm.get_cmap("tab10")

    # Create flight segments (each leg between waypoints)
    flight_lines = []
    flight_labels = []
    flight_colors = []

    for flight_idx, flight in enumerate(flights):
        # Get color from the palette
        color = matplotlib.colors.rgb2hex(cmap(flight_idx % cmap.N))

        # Create segments between consecutive waypoints
        for i in range(len(flight) - 1):
            origin = flight[i]
            dest = flight[i + 1]

            line = LineString(
                [(airports[origin]["lon"], airports[origin]["lat"]), (airports[dest]["lon"], airports[dest]["lat"])]
            )
            flight_lines.append(line)

            # Label shows the full route
            full_route = " → ".join(flight)
            segment_label = f"{origin} → {dest} (part of {full_route})"
            flight_labels.append(segment_label)
            flight_colors.append(color)

    flights_gdf = gpd.GeoDataFrame(
        {"route": flight_labels, "color": flight_colors}, geometry=flight_lines, crs="EPSG:4326"
    )

    # Create airports (deduplicated from all waypoints)
    airport_points = []
    airport_codes = []
    seen_codes = set()

    for flight in flights:
        for code in flight:
            if code not in seen_codes:
                airport_points.append(Point(airports[code]["lon"], airports[code]["lat"]))
                airport_codes.append(code)
                seen_codes.add(code)

    airports_gdf = gpd.GeoDataFrame({"code": airport_codes}, geometry=airport_points, crs="EPSG:4326")

    return flights_gdf, airports_gdf


def create_interactive_map(flights_gdf, airports_gdf):
    """Create interactive Folium map and return as HTML string"""
    import folium

    # Create base map
    m = folium.Map(location=[30.0, 0.0], zoom_start=2)

    # Add each flight path with its color
    for idx, row in flights_gdf.iterrows():
        folium.PolyLine(
            locations=[(coord[1], coord[0]) for coord in row.geometry.coords],
            color=row["color"],
            weight=3,
            opacity=0.7,
            tooltip=row["route"],
        ).add_to(m)

    # Add airports
    for idx, row in airports_gdf.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=8,
            color="blue",
            fill=True,
            fillColor="blue",
            fillOpacity=0.7,
            tooltip=row["code"],
        ).add_to(m)

    return m.get_root().render().encode("utf-8")


def create_static_map(flights_gdf, airports_gdf):
    """Create static PNG map cropped to flight area and return as bytes"""
    # Load world map
    world = gpd.read_file("https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip")

    # Calculate bounds from all geometries
    all_bounds = gpd.GeoDataFrame(pd.concat([flights_gdf, airports_gdf], ignore_index=True))
    minx, miny, maxx, maxy = all_bounds.total_bounds

    # Add padding (10% on each side)
    padding_x = (maxx - minx) * 0.1
    padding_y = (maxy - miny) * 0.1

    fig, ax = plt.subplots(figsize=(15, 10))

    # Plot world map
    world.plot(ax=ax, color="lightgray", edgecolor="black", linewidth=0.5)

    # Plot flight paths with colors from the dataframe
    flights_gdf.plot(ax=ax, color=flights_gdf["color"], linewidth=2, alpha=0.7, zorder=2)

    # Plot airports
    airports_gdf.plot(ax=ax, color="blue", markersize=100, alpha=0.9, zorder=3)

    # Add airport labels
    for _, row in airports_gdf.iterrows():
        ax.annotate(
            row["code"],
            xy=(row.geometry.x, row.geometry.y),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=10,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
        )

    # Crop to flight area
    ax.set_xlim(minx - padding_x, maxx + padding_x)
    ax.set_ylim(miny - padding_y, maxy + padding_y)

    plt.title("Flight Paths", fontsize=16, fontweight="bold")
    ax.set_axis_off()

    # Save to BytesIO buffer in memory
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buffer.seek(0)
    return buffer.read()
```

</details>

## Step 3: Add tool to agent

Now we can add a new tool to our agent:

```python
from agentstack_agents.visualize import prepare_flight_data, create_static_map, create_interactive_map


@server.agent()
async def flight_search_agent():
    ...

    # variables to store output of the visualization
    static_png_bytes = None
    interactive_html_bytes = None

    # create a framework tool to visualize flights
    @tool
    async def visualize_flights(flights: list[list[str]]) -> None:
        """
        Tool that visualizes flights and saves them to a file. Use to visualize all flights from search results.
        Args:
            flights: A list of flights with waypoints (list of airport codes), for example,
                [
                    ["PRG", "LAS"],  # Direct flight
                    ["JFK", "LHR", "DXB", "SIN"],  # Flight with 2 layovers
                    # Add more flights here
                ]
        """
        nonlocal static_png_bytes, interactive_html_bytes
        # Define your flights with waypoints (list of airport codes)
        flights_gdf, airports_gdf = prepare_flight_data(flights)
        static_png_bytes = create_static_map(flights_gdf, airports_gdf)
        interactive_html_bytes = create_interactive_map(flights_gdf, airports_gdf)

    async for event, meta in RequirementAgent(
            llm=llm,
            tools=[*kiwi_tools, ensure_all_data, visualize_flights],
            requirements=[
                ConditionalRequirement(ensure_all_data, force_at_step=1),
                ConditionalRequirement(visualize_flights, force_after=kiwi_tools),
            ],
    ).run(prompt):
        ...

```

When tool is called, it will populate the variables `static_png_bytes` and `interactive_html_bytes` with the
raw file content. We will now send them to the user using Agent Stack Files API. First, add the PlatformAPIExtension
which does all the heavy lifting to negotiate Agent Stack token and automatically configures the Agent Stack
SDK.

```python
from agentstack_sdk.a2a.extensions import PlatformApiExtensionServer, PlatformApiExtensionSpec


@server.agent()
async def flight_search_agent(
        ...,
        _: Annotated[PlatformApiExtensionServer, PlatformApiExtensionSpec()],
):
    ...
```

## Step 4: Upload and return files

Now we can upload the HTML file using the `File` class from the SDK. We will send the PNG file cirectly as bytes
because we want it to show up in the agent response content.

```python
if static_png_bytes is not None:
    # Send PNG directly as base64 encoded string
    base64_string = base64.b64encode(static_png_bytes).decode("utf-8")
    file_part = FilePart(file=FileWithBytes(bytes=base64_string, mime_type="image/png", name="flights.png"))
    yield file_part

if interactive_html_bytes is not None:
    # Upload HTML file to the Agent Stack server and send it using the Agent Stack SDK
    file = await File.create(filename="flights.html", content=interactive_html_bytes, content_type="text/html")
    yield file.to_file_part()

```

Now we are ready to make the visualizations configurable **[05-add-settings](./05-add-settings.md)**