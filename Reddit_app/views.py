from django.shortcuts import render
from Reddit_app.plotydash import generate_layout
from plotly.offline import plot
from plotly.graph_objs import Scatter
from . import old_app

def dashboard_view(request):
    print ("in the dashboard_view")
    server_name='Zilliqa'
    dir='./Reddit_app/assets/'+server_name

    #layout_dash=generate_layout(dir)
    #print (layout)

    layout_dir='./Reddit_app/assets/Zilliqa/master.html'
    with open(layout_dir) as f:
        layout = f.read()
    print (layout)


    """
    x_data = [0,1,2,3]
    y_data = [x**2 for x in x_data]
    plot_div = plot([Scatter(x=x_data, y=y_data,
                        mode='lines', name='test',
                        opacity=0.8, marker_color='green')],
               output_type='div')
    """

    old_app.update_layout(server_name)
    return render(request, "Reddit_app/dashboard.html", context={'plot_div': layout})


def intro_page(request):
    return none