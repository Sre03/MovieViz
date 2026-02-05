import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="The MovieLens Spotlight: Visualizing Viewer Preferences",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Modern Styling ---
st.markdown("""
    <style>
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* =========================
   MULTISELECT (SELECTED GENRES)
   ========================= */

    /* Selected genre pills */
    section[data-testid="stSidebar"] span[data-baseweb="tag"] {
        background-color: #2563eb !important;   /* Blue */
        color: white !important;
        border-radius: 6px;
    }
    
    /* Remove (x) icon inside pill */
    section[data-testid="stSidebar"] span[data-baseweb="tag"] svg {
        color: white !important;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #ff4b4b, transparent);
    }
    
    /* Headers */
    h1 {
        font-size: 3rem !important;
        font-weight: 800 !important;
        letter-spacing: -1px;
    }
    
    h3 {
        font-weight: 600;
        margin-top: 1.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Data Loading and Caching ---
@st.cache_data
def load_data():
    """Loads, cleans, and transforms the MovieLens 100k u.item data."""
    COLUMN_NAMES = [
        'movie_id', 'title', 'release_date', 'video_release_date', 'imdb_url',
        'unknown', 'Action', 'Adventure', 'Animation', 'Children\'s', 'Comedy',
        'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror',
        'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western'
    ]
    df = pd.read_csv('u.item', sep='|', names=COLUMN_NAMES, encoding='latin-1')

    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['year'] = df['release_date'].dt.year
    df.dropna(subset=['year'], inplace=True)
    df['year'] = df['year'].astype(int)

    genre_columns = df.columns[6:25]
    df_melted = df.melt(
        id_vars=['movie_id', 'title', 'year'],
        value_vars=genre_columns,
        var_name='genre',
        value_name='is_genre'
    )
    df_genres = df_melted[df_melted['is_genre'] == 1].drop(columns='is_genre')

    return df, df_genres

df_movies, df_genres = load_data()

# --- Dashboard Title ---
st.title("🎬 MovieLens Cinema Explorer")
st.markdown("### *Movie Space Navigator - https://sre03.github.io/MovieViz/ \n Find movies to watch based on the genre of your choice - an interactive visualizer*")
st.markdown("### **")
st.markdown("### *Discover patterns in movie releases, genres, and cinematic trends over time*")


# --- Sidebar Filters ---
st.sidebar.header("🎯 Filters")
st.sidebar.markdown("---")

min_year, max_year = int(df_movies['year'].min()), int(df_movies['year'].max())
selected_year_range = st.sidebar.slider(
    "📅 Release Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

all_genres = sorted(df_genres['genre'].unique())
selected_genres = st.sidebar.multiselect(
    "🎭 Select Genres",
    options=all_genres,
    default=all_genres
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Dataset Info")
st.sidebar.info(f"**Total Movies:** {len(df_movies):,}")
st.sidebar.info(f"**Total Genres:** {len(all_genres)}")

# --- Filtering Logic ---
filtered_movies = df_movies[
    (df_movies['year'] >= selected_year_range[0]) &
    (df_movies['year'] <= selected_year_range[1])
]

if selected_genres:
    movie_ids_with_selected_genres = df_genres[df_genres['genre'].isin(selected_genres)]['movie_id'].unique()
    filtered_movies = filtered_movies[filtered_movies['movie_id'].isin(movie_ids_with_selected_genres)]
    filtered_genres = df_genres[df_genres['movie_id'].isin(filtered_movies['movie_id'])]
else:
    filtered_genres = pd.DataFrame(columns=df_genres.columns)

# --- Key Performance Indicators ---
st.markdown("## 📊 Overview Metrics")

total_movies_filtered = filtered_movies.shape[0]
time_span_filtered = f"{selected_year_range[0]} - {selected_year_range[1]}"
total_unique_genres_filtered = filtered_genres[filtered_genres['genre'].isin(selected_genres)]['genre'].nunique()
avg_year = int(filtered_movies['year'].mean()) if not filtered_movies.empty else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(label="🎥 Total Movies", value=f"{total_movies_filtered:,}")
kpi2.metric(label="📆 Time Span", value=time_span_filtered)
kpi3.metric(label="🎭 Active Genres", value=total_unique_genres_filtered)
kpi4.metric(label="📈 Avg Release Year", value=avg_year)

st.markdown("---")

# --- Main Visualizations ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📅 Movie Releases by Year")
    releases_by_year = filtered_movies['year'].value_counts().sort_index()
    
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=releases_by_year.index,
        y=releases_by_year.values,
        marker=dict(
            color=releases_by_year.values,
            #colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Movies", thickness=15)
        ),
        hovertemplate='<b>Year:</b> %{x}<br><b>Movies:</b> %{y}<extra></extra>'
    ))
    
    fig1.update_layout(
        xaxis=dict(title='Year'),
        yaxis=dict(title='Number of Movies'),
        height=420,
        hovermode='x unified',
        margin=dict(l=50, r=50, t=30, b=50)
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("### 🎭 Top Genres Distribution")
    genre_counts = filtered_genres[filtered_genres['genre'].isin(selected_genres)]['genre'].value_counts()
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        y=genre_counts.index,
        x=genre_counts.values,
        orientation='h',
        marker=dict(
            color=genre_counts.values,
            #colorscale='Plasma',
            showscale=True,
            colorbar=dict(title="Movies", thickness=15)
        ),
        hovertemplate='<b>%{y}</b><br>Movies: %{x}<extra></extra>'
    ))
    
    fig2.update_layout(
        xaxis=dict(title='Number of Movies'),
        yaxis=dict(title='Genre', categoryorder='total ascending'),
        height=420,
        margin=dict(l=100, r=50, t=30, b=50)
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("### 📈 Genre Trends Over Time")
genre_trends = filtered_genres[filtered_genres['genre'].isin(selected_genres)] \
    .groupby(['year', 'genre']).size().reset_index(name='count')

fig3 = px.area(
    genre_trends,
    x='year',
    y='count',
    color='genre',
    labels={'year': 'Year', 'count': 'Number of Movies', 'genre': 'Genre'},
    height=500,
    color_discrete_sequence=px.colors.qualitative.Bold
)

fig3.update_layout(
    hovermode='x unified',
    margin=dict(l=50, r=50, t=30, b=50)
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("### 🔥 Genre Co-occurrence Heatmap")
st.markdown("*Shows the ratio of movies where genres appear together*")

if not filtered_movies.empty and selected_genres:
    genre_pivot = filtered_genres[filtered_genres['genre'].isin(selected_genres)] \
        .pivot_table(index='movie_id', columns='genre', aggfunc='size', fill_value=0)

    # Calculate co-occurrence counts
    co_occurrence = genre_pivot.T.dot(genre_pivot)
    
    # Convert to ratios: divide each cell by the diagonal (total count for that genre)
    genre_totals = co_occurrence.values.diagonal()
    co_occurrence_ratio = co_occurrence.values / genre_totals[:, None]
    
    # Convert to percentage for better readability
    co_occurrence_ratio = co_occurrence_ratio * 100

    fig4 = go.Figure(data=go.Heatmap(
        z=co_occurrence_ratio,
        x=co_occurrence.columns,
        y=co_occurrence.index,
        #colorscale='RdYlBu_r',
        hovertemplate='<b>%{y}</b> & <b>%{x}</b><br>Co-occurrence: %{z:.1f}%<extra></extra>',
        colorbar=dict(title="% Co-occurrence", thickness=15),
        zmin=0,
        zmax=100
    ))
    
    fig4.update_layout(
        xaxis=dict(tickangle=-45, side='bottom'),
        yaxis=dict(tickangle=0),
        height=600,
        margin=dict(l=150, r=50, t=50, b=150)
    )
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.warning("⚠️ Please select at least one genre to display the co-occurrence heatmap.")

# --- Footer ---
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #888; padding: 20px;'>
        <p>📊 Built with Streamlit & Plotly | 🎬 Data: MovieLens 100k Dataset</p>
    </div>
""", unsafe_allow_html=True)
