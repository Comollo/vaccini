import altair as alt
import pandas as pd
import streamlit as st

# Read data
vaccine = pd.read_csv("https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/anagrafica"
                      "-vaccini-summary-latest.csv")

population = pd.read_csv("population_istat.csv")

# Preprocessing
vaccine_filtered = vaccine[["fascia_anagrafica", "sesso_maschile", "sesso_femminile"]]
df = population.merge(vaccine_filtered, left_on="fasce", right_on="fascia_anagrafica")

df.drop(columns=["fascia_anagrafica"], inplace=True)
df.rename(columns={"sesso_maschile": "vaccini_maschi", "sesso_femminile": "vaccini_femmine"}, inplace=True)
df_stacked = df.set_index("fasce").stack().reset_index()
df_stacked.rename(columns={"level_1": "cat", 0: "value"}, inplace=True)
df_female = df_stacked.loc[(df_stacked["cat"] == "femmine") | (df_stacked["cat"] == "vaccini_femmine")]
df_male = df_stacked.loc[(df_stacked["cat"] == "maschi") | (df_stacked["cat"] == "vaccini_maschi")]
merged = df_male.merge(df_female, on="fasce")
df_to_display = merged.loc[
    ((merged["cat_x"] == "maschi") & (merged["cat_y"] == "femmine")) |
    ((merged["cat_x"] == "vaccini_maschi") & (merged["cat_y"] == "vaccini_femmine"))
    ]

final = df_to_display.copy()
final.rename(columns={"cat_x": "Male",
                      "cat_y": "Female",
                      "value_x": "Value_male",
                      "value_y": "Value_female"}, inplace=True)

final.replace({'maschi': 'Male population',
               "femmine": "Female population",
               "vaccini_maschi": "Male vaccine",
               "vaccini_femmine": "Female vaccine"}, inplace=True)

source = final

scale_color = alt.Scale(domain=['Female population', 'Female vaccine', 'Male population', 'Male vaccine'],
                        range=['#FFCCD5', "red", 'lightblue', "red"])

selection_female = alt.selection_multi(fields=['Female'])
# color_female = alt.condition(selection_female,
#                       alt.Color('Female:O', legend=None, scale=scale_color),
#                       alt.value('lightpink'))

selection_male = alt.selection_multi(fields=['Male'])
# color_male = alt.condition(selection_male,
#                       alt.Color('Male:O', legend=None, scale=scale_color),
#                       alt.value('lightblue'))


base = alt.Chart(source).properties(
    width=300,
    height=400
)

left = base.encode(
    y=alt.Y('fasce:O', axis=None),
    x=alt.X('Value_female:Q',
            title='population',
            sort=alt.SortOrder('descending'), stack=None),
    color=alt.Color('Female:O', legend=None, scale=scale_color),
    opacity=alt.condition(selection_female, alt.value(1), alt.value(0.2)),
    tooltip=[alt.Tooltip('Value_female', title='Tot')]
).mark_bar().properties(title='Female').add_selection(selection_female)

middle = base.encode(
    y=alt.Y('fasce:O', axis=None),
    text=alt.Text('fasce:O'),
).mark_text().properties(width=35)

right = base.encode(
    y=alt.Y('fasce:O', axis=None),
    x=alt.X('Value_male:Q', title='population', stack=None),
    color=alt.Color('Male:O', legend=None, scale=scale_color),
    opacity=alt.condition(selection_male, alt.value(1), alt.value(0.2)),
    tooltip=[alt.Tooltip('Value_male', title='Tot')]
).mark_bar().properties(title='Male').add_selection(selection_male)

pop = alt.concat(left, middle, right, spacing=5)

legend_female = alt.Chart(final).mark_point().encode(
    y=alt.Y('Female:O', axis=alt.Axis(orient='right'), title=None),
    color=alt.Color('Female:O', legend=None, scale=scale_color)
).add_selection(
    selection_female
)

legend_male = alt.Chart(final).mark_point().encode(
    y=alt.Y('Male:O', axis=alt.Axis(orient='right'), title=None),
    color=alt.Color('Male:O', legend=None, scale=scale_color)
).add_selection(
    selection_male
)

legend = legend_female & legend_male

fig = pop | legend

st.write(
    """
    # Population Pyramid and Vaccine Progress
    """
)

st.sidebar.header("Info")
st.sidebar.markdown("this pyramid shows the progress of vaccination in Italy by age category.")

st.altair_chart(fig, use_container_width=True)

if st.checkbox('Show dataframe'):
    final