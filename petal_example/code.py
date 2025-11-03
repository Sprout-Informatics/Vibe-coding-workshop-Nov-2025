from seaborn import load_dataset
df = load_dataset('iris')
import altair as alt

chart = alt.Chart(df).mark_circle().encode(
    x=alt.X('petal_length', title='Petal Length (cm)'),
    y=alt.Y('petal_width', title='Petal Width (cm)'),
    color='species',
    tooltip=['petal_length', 'petal_width', 'species']
).properties(
    title='Petal Length vs. Petal Width by Species'
).interactive()

chart.display()
