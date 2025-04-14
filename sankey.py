import pandas as pd
import plotly.graph_objects as go

df = pd.read_csv("movies_cleaned1.csv")

# Preprocess data
df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
df["budget"] = pd.to_numeric(df["budget"], errors="coerce")
df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
df["genres"] = df["genres"].fillna("").apply(lambda x: x.split(", ")[0] if x else None)


def create_sankey_for_decade(df, start_year, end_year, output_filename):
    # Filter by decade
    df_decade = df[
        (df["release_date"].dt.year >= start_year) &
        (df["release_date"].dt.year <= end_year)
    ].dropna(subset=["budget", "revenue", "genres"])

    # Get top 10 genres for this decade
    top_genres = df_decade["genres"].value_counts().nlargest(10).index
    df_decade = df_decade[df_decade["genres"].isin(top_genres)]

    # no NaN or infinite values
    df_decade["budget"] = df_decade["budget"].apply(pd.to_numeric, errors='coerce')
    df_decade["revenue"] = df_decade["revenue"].apply(pd.to_numeric, errors='coerce')
    df_decade = df_decade.dropna(subset=["budget", "revenue"])

    # Round budget and revenue to the nearest million
    df_decade["budget_rounded"] = (df_decade["budget"] / 1e6).round() * 1e6
    df_decade["revenue_rounded"] = (df_decade["revenue"] / 1e6).round() * 1e6

    # Create bins for budget and revenue with more readable labels
    budget_bins = [0, 10e6, 50e6, 100e6, 200e6, 500e6, float("inf")]
    revenue_bins = [0, 10e6, 50e6, 100e6, 200e6, 500e6, float("inf")]

    budget_labels = ["$10M", "$50M", "$100M", "$200M", "$500M", "$500M+"]
    revenue_labels = ["$10M", "$50M", "$100M", "$200M", "$500M", "$500M+"]

    # Categorize budget and revenue into bins
    df_decade["budget_bin"] = pd.cut(df_decade["budget_rounded"], budget_bins, labels=budget_labels, include_lowest=True)
    df_decade["revenue_bin"] = pd.cut(df_decade["revenue_rounded"], revenue_bins, labels=revenue_labels, include_lowest=True)

    # Group data for Sankey flows
    df_grouped = df_decade.groupby(["budget_bin", "genres"]).size().reset_index(name="count")
    df_grouped_rev = df_decade.groupby(["genres", "revenue_bin"]).size().reset_index(name="count")

    # Create links for budget to genre
    links = {
        "source": [],
        "target": [],
        "value": []
    }

    # Define indices for nodes
    budget_indices = {val: i for i, val in enumerate(budget_labels)}
    genre_indices = {val: i + len(budget_indices) for i, val in enumerate(top_genres)}
    revenue_indices = {val: i + len(budget_indices) + len(genre_indices) for i, val in enumerate(revenue_labels)}

    # Budget -> Genre links
    for _, row in df_grouped.iterrows():
        links["source"].append(budget_indices[row["budget_bin"]])
        links["target"].append(genre_indices[row["genres"]])
        links["value"].append(row["count"])

    # Genre -> Revenue links
    for _, row in df_grouped_rev.iterrows():
        links["source"].append(genre_indices[row["genres"]])
        links["target"].append(revenue_indices[row["revenue_bin"]])
        links["value"].append(row["count"])

    # Create Sankey diagram
    labels = list(budget_labels) + list(top_genres) + list(revenue_labels)
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
        ),
        link=dict(
            source=links["source"],
            target=links["target"],
            value=links["value"]
        ))])

    fig.update_layout(title_text=f"Sankey Diagram: Budget → Genre → Revenue ({start_year}-{end_year})", font_size=10)

    # show Sankey
    fig.show()

    # save Sankey as HTML
    fig.write_html(output_filename)

create_sankey_for_decade(df, 2000, 2009, "sankey_2000s.html")
create_sankey_for_decade(df, 2010, 2019, "sankey_2010s.html")
create_sankey_for_decade(df, 2020, 2029, "sankey_2020s.html")
