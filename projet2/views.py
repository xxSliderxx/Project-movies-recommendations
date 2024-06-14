from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import io
from django.core.cache import cache
import plotly.express as px
import plotly.io as pio
def acceuil(request):
    

    return render(request, 'projet2/Acceuil.html')

def analyse(request):
    return render(request, 'projet2/Tout.html')
    

def movie(request):
    cache_key = 'Boxplot_csv'
    csv_data = cache.get(cache_key)

    if csv_data is None:
        with open('Boxplot.csv', 'r', encoding='utf-8') as f:
            csv_data = f.read()
            cache.set(cache_key, csv_data, timeout=60 * 15)

    df = pd.read_csv(io.StringIO(csv_data))
    date = ['1888-1915', '1916-1943', '1944-1971', '1972-1999', '2000-2028']
    
    
    fig = px.box(
        data_frame=df,
        x= "Period",
        y="averageRating", 
        width=700, 
        height=700, 
        category_orders={"Period": date},
        labels={"Period": " ", "averageRating": "Notes"}
    )
    fig.update_layout(
        title_text="Répartition des notes des films et téléfilms par périodes", 
        title_x=0.5
    )
    plot_html = pio.to_html(fig, full_html=False)
    

    return render(request, 'projet2/Movies.html', {'plot_html': plot_html})

def short(request):
    

    return render(request, 'projet2/Short.html')

def series(request):
    

    return render(request, 'projet2/Series.html')

def index(request):
    template = loader.get_template("projet2/galere.html")

    cache_key = 'Matrice_csv'
    csv_data = cache.get(cache_key)

    if csv_data is None:
        with open('Matrice.csv', 'r', encoding='utf-8') as f:
            csv_data = f.read()
            cache.set(cache_key, csv_data, timeout=60 * 15)

    df = pd.read_csv(io.StringIO(csv_data))
    
    df = df.reset_index(drop =True)

    context = {
        'df': df
    }

    return HttpResponse(template.render(context, request))

def search(request):
    query = request.GET.get('query', '')

    if query:
        cache_key = 'Matrice_csv'
        csv_data = cache.get(cache_key)

        if csv_data is None:
            with open('Matrice.csv', 'r', encoding='utf-8') as f:
                csv_data = f.read()
                cache.set(cache_key, csv_data, timeout=60 * 15)

        df = pd.read_csv(io.StringIO(csv_data))
        df['runtimeMinutes'].fillna(0,inplace = True)
        df['runtimeMinutes'] = df['runtimeMinutes'].astype('int64')
        zero = df[df['runtimeMinutes']== 0].index
        df.drop(index = zero,inplace = True)
        
        df = df.reset_index(drop =True)

        results = df[df['title'] == query]    
        
        if results.empty:
            return render(request, 'projet2/galere.html', {'query': query, 'no_results': True})
        
        results = results.select_dtypes('number').dropna()
        id = results.index

        X = df.select_dtypes('number')
        X = X.dropna()
        scaler = StandardScaler().fit(X)
        X_scaled = pd.DataFrame(scaler.transform(X), index=X.index, columns=X.columns)

        modelNN = NearestNeighbors().fit(X_scaled)
        indiv_concerne_scaled = X_scaled.loc[id]
        indiv_concerne = X.loc[id]
        neigh_dist, neigh_mov = modelNN.kneighbors(indiv_concerne_scaled, n_neighbors=11)
        mov_ressem = neigh_mov[0][1:]
        x = X.iloc[mov_ressem].index

        Res = df.iloc[x]
        base = "https://image.tmdb.org/t/p/original"
        for index, row in Res.iterrows():
            if pd.notnull(row['poster_path']):
                Res.at[index, 'poster_url'] = f"{base}{row['poster_path']}"
            else:
                Res.at[index, 'poster_url'] = None
                
        Res2 = df.iloc[id]       
        for index, row in Res2.iterrows():
            if pd.notnull(row['poster_path']):
                Res2.at[index, 'poster_url'] = f"{base}{row['poster_path']}"
            else:
                Res2.at[index, 'poster_url'] = None
        

        return render(request, 'projet2/galere.html',{'results': results.to_dict(orient='records'), 'query': query, 'columns': results.columns, 'Res': Res.to_dict(orient='records'),'Res2': Res2.to_dict(orient='records')})

    return render(request, 'projet2/galere.html', {'query': query})
